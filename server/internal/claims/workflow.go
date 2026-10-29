package claims

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"

	"github.com/datasektionen/cashflow/server/internal/database/db"
)

// Cashflow 3 dates workflow steps in Swedish local time (Django's localdate).
var stockholm = mustLoadLocation("Europe/Stockholm")

func mustLoadLocation(name string) *time.Location {
	loc, err := time.LoadLocation(name)
	if err != nil {
		panic(err)
	}
	return loc
}

func today() pgtype.Date {
	y, m, d := time.Now().In(stockholm).Date()
	return pgtype.Date{Time: time.Date(y, m, d, 0, 0, 0, 0, time.UTC), Valid: true}
}

// change is one workflow transaction on a locked claim.
type change struct {
	q      *db.Queries
	claim  db.LockClaimRow
	state  State
	viewer Viewer
	actor  db.GetActorRow
}

// withClaim runs fn in a transaction with the claim locked, after checking
// the viewer may see it at all.
func (s *Store) withClaim(ctx context.Context, v Viewer, kind Kind, number int64, fn func(c *change) error) error {
	summary, err := s.Get(ctx, v, kind, number)
	if err != nil {
		return err
	}
	return pgx.BeginFunc(ctx, s.pool, func(tx pgx.Tx) error {
		c, err := lock(ctx, db.New(tx), v, summary)
		if err != nil {
			return err
		}
		return fn(c)
	})
}

// lock locks a claim the viewer may see inside a transaction and reads the
// state the rules need.
func lock(ctx context.Context, q *db.Queries, v Viewer, summary Summary) (*change, error) {
	claim, err := q.LockClaim(ctx, summary.ID)
	if err != nil {
		return nil, fmt.Errorf("lock claim: %w", err)
	}
	actor, err := q.GetActor(ctx, v.Username)
	if err != nil {
		return nil, fmt.Errorf("actor: %w", err)
	}
	parts, err := q.ListPartStates(ctx, claim.ID)
	if err != nil {
		return nil, fmt.Errorf("parts: %w", err)
	}
	state := State{
		Kind:      Kind(claim.Type.String),
		Owner:     summary.Owner.Username,
		Flagged:   claim.IsFlagged.Bool,
		Confirmed: claim.ConfirmedByID.Valid,
		Paid:      claim.ReimbursementID.Valid || claim.PaidByID.Valid || claim.PaidAt.Valid,
	}
	for _, p := range parts {
		state.Parts = append(state.Parts, PartState{ID: p.ID, CostCentre: p.CostCentre, Attested: p.Attested})
	}
	return &change{q: q, claim: claim, state: state, viewer: v, actor: actor}, nil
}

// State returns the rule state of a claim the viewer may see, for Actions.
func (s *Store) State(ctx context.Context, v Viewer, summary Summary) (State, error) {
	parts, err := s.Queries.ListPartStates(ctx, summary.ID)
	if err != nil {
		return State{}, err
	}
	state := State{
		Kind: summary.Kind, Owner: summary.Owner.Username, Flagged: summary.Flagged,
		Confirmed: summary.Confirmed, Paid: summary.Paid,
	}
	for _, p := range parts {
		state.Parts = append(state.Parts, PartState{ID: p.ID, CostCentre: p.CostCentre, Attested: p.Attested})
	}
	return state, nil
}

func (c *change) part(id int64) (PartState, error) {
	for _, p := range c.state.Parts {
		if p.ID == id {
			return p, nil
		}
	}
	return PartState{}, ErrPartNotOnClaim
}

// SetAttested attests or unattests one part, writing Cashflow 3's comment.
func (s *Store) SetAttested(ctx context.Context, v Viewer, kind Kind, number, partID int64, attested bool) error {
	return s.withClaim(ctx, v, kind, number, func(c *change) error {
		p, err := c.part(partID)
		if err != nil {
			return err
		}
		if attested {
			err = v.CanAttest(c.state, p)
		} else {
			err = v.CanUnattest(c.state, p)
		}
		if err != nil {
			return err
		}
		locked, err := c.q.LockPart(ctx, partID)
		if err != nil {
			return err
		}
		params := db.SetPartAttestationParams{ID: partID}
		verb := "Avattesterar"
		if attested {
			params.ProfileID = pgtype.Int8{Int64: c.actor.ProfileID, Valid: true}
			params.OnDate = today()
			verb = "Attesterar"
		}
		if err := c.q.SetPartAttestation(ctx, params); err != nil {
			return err
		}
		// ClaimPart.__str__: "<description> (<budget line>: <amount> kr)".
		label := fmt.Sprintf("%s (%s: %s kr)", c.claim.Description, locked.BudgetLine, decimalKronor(locked.AmountOre))
		return s.comment(ctx, c, fmt.Sprintf("%s kvittodelen ```%s```", verb, label))
	})
}

// SetConfirmed confirms or unconfirms an expense's receipt.
func (s *Store) SetConfirmed(ctx context.Context, v Viewer, number int64, confirmed bool) error {
	return s.withClaim(ctx, v, Expense, number, func(c *change) error {
		if confirmed {
			if err := v.CanConfirm(c.state); err != nil {
				return err
			}
			if err := c.q.SetConfirmation(ctx, db.SetConfirmationParams{
				ID: c.claim.ExpenseDataID.Int64, UserID: pgtype.Int4{Int32: c.actor.UserID, Valid: true}, OnDate: today(),
			}); err != nil {
				return err
			}
			return s.comment(ctx, c, "Jag har bekräftat kvittots giltighet.")
		}
		// Cashflow 3 leaves no comment when unconfirming.
		if err := v.CanUnconfirm(c.state); err != nil {
			return err
		}
		return c.q.SetConfirmation(ctx, db.SetConfirmationParams{ID: c.claim.ExpenseDataID.Int64})
	})
}

// SetFlagged flags an expense for its owner to fix, or clears the flag.
func (s *Store) SetFlagged(ctx context.Context, v Viewer, number int64, flagged bool) error {
	return s.withClaim(ctx, v, Expense, number, func(c *change) error {
		if err := v.CanSetFlag(c.state, flagged); err != nil {
			return err
		}
		return c.q.SetFlagged(ctx, db.SetFlaggedParams{ID: c.claim.ExpenseDataID.Int64, Flagged: flagged})
	})
}

// PayInvoice records an invoice as paid today by the viewer.
func (s *Store) PayInvoice(ctx context.Context, v Viewer, number int64) error {
	return s.withClaim(ctx, v, Invoice, number, func(c *change) error {
		if err := v.CanPayInvoice(c.state); err != nil {
			return err
		}
		if err := c.q.SetInvoicePaid(ctx, db.SetInvoicePaidParams{
			ID: c.claim.InvoiceDataID.Int64, ProfileID: pgtype.Int8{Int64: c.actor.ProfileID, Valid: true}, OnDate: today(),
		}); err != nil {
			return err
		}
		return s.comment(ctx, c, fmt.Sprintf("Betalade fakturan ```%s```", c.claim.Description))
	})
}

// AddComment adds the viewer's comment; anyone who can see a claim may comment.
func (s *Store) AddComment(ctx context.Context, v Viewer, kind Kind, number int64, body string) error {
	body = strings.TrimSpace(body)
	if body == "" {
		return ErrEmptyComment
	}
	return s.withClaim(ctx, v, kind, number, func(c *change) error {
		return s.comment(ctx, c, body)
	})
}

// Delete removes a claim with its parts, files and comments. The files stay
// in S3, as in Cashflow 3.
func (s *Store) Delete(ctx context.Context, v Viewer, kind Kind, number int64) error {
	return s.withClaim(ctx, v, kind, number, func(c *change) error {
		if err := v.CanDelete(c.state); err != nil {
			return err
		}
		id := c.claim.ID
		for _, step := range []func(context.Context, int64) error{
			c.q.DeleteClaimComments, c.q.DeleteClaimFiles, c.q.DeleteClaimParts, c.q.DeleteClaim,
		} {
			if err := step(ctx, id); err != nil {
				return err
			}
		}
		if c.claim.ExpenseDataID.Valid {
			return c.q.DeleteExpenseData(ctx, c.claim.ExpenseDataID.Int64)
		}
		return c.q.DeleteInvoiceData(ctx, c.claim.InvoiceDataID.Int64)
	})
}

// comment writes a comment by the actor and, unless they own the claim,
// queues an email to the owner, as Cashflow 3's SpamMail.on_comment does for
// every comment, including the workflow ones.
func (s *Store) comment(ctx context.Context, c *change, body string) error {
	if err := c.q.InsertComment(ctx, db.InsertCommentParams{ClaimID: c.claim.ID, AuthorID: c.actor.ProfileID, Content: body}); err != nil {
		return fmt.Errorf("comment: %w", err)
	}
	owner, err := c.q.GetCommentRecipient(ctx, c.claim.ID)
	if err != nil {
		return err
	}
	if owner.Username == c.viewer.Username || owner.Email == "" {
		return nil
	}
	author, err := c.q.GetPersonName(ctx, c.viewer.Username)
	if err != nil {
		return err
	}
	mail := commentEmail(s.publicURL, Kind(c.claim.Type.String), number(c.claim), c.claim.Description, owner, author, body)
	payload, err := json.Marshal(mail)
	if err != nil {
		return err
	}
	return c.q.EnqueueEmail(ctx, payload)
}

func number(c db.LockClaimRow) int64 {
	if c.ExpenseDataID.Valid {
		return c.ExpenseDataID.Int64
	}
	return c.InvoiceDataID.Int64
}

// decimalKronor formats öre the way Python prints a Decimal(9, 2): "123.45".
func decimalKronor(ore int64) string {
	sign := ""
	if ore < 0 {
		sign, ore = "-", -ore
	}
	return fmt.Sprintf("%s%d.%02d", sign, ore/100, ore%100)
}

// IsProblem reports whether err is a rule violation, as opposed to a failure.
func IsProblem(err error) (*Problem, bool) {
	var p *Problem
	return p, errors.As(err, &p)
}

func pgInt8(v int64) pgtype.Int8 { return pgtype.Int8{Int64: v, Valid: true} }
