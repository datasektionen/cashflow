package claims

import (
	"context"
	"fmt"
	"slices"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"

	"github.com/datasektionen/cashflow/server/internal/database/db"
)

// Input is a claim as the create and edit forms send it.
type Input struct {
	Description string
	// Date is the expense date (required) or the invoice date (optional).
	Date          *time.Time
	InvoiceNumber string
	DueDate       *time.Time
	Parts         []PartInput
	// UploadIDs are files uploaded beforehand (POST /files) to attach.
	UploadIDs []string
	// RemoveFileIDs are attached files to remove (editing only).
	RemoveFileIDs []int64
}

type PartInput struct {
	CostCentre          string
	SecondaryCostCentre string
	BudgetLine          string
	AmountOre           int64
}

// Violation is a problem with one input field; Field uses the form's names
// in snake case, e.g. "parts[1].amount_ore".
type Violation struct{ Field, Code string }

// InvalidInput lists everything wrong with an input at once, so the form can
// mark every field in one go.
type InvalidInput struct{ Violations []Violation }

func (e *InvalidInput) Error() string {
	return fmt.Sprintf("claims: %d invalid fields", len(e.Violations))
}

// core_claimpart.amount is numeric(9, 2): below ten million kronor.
const maxAmountOre = 1_000_000_000 - 1

func (in *Input) normalise() {
	in.Description = strings.TrimSpace(in.Description)
	in.InvoiceNumber = strings.TrimSpace(in.InvoiceNumber)
	for i := range in.Parts {
		p := &in.Parts[i]
		p.CostCentre = strings.TrimSpace(p.CostCentre)
		p.SecondaryCostCentre = strings.TrimSpace(p.SecondaryCostCentre)
		p.BudgetLine = strings.TrimSpace(p.BudgetLine)
	}
}

// validate checks an input; creating also needs at least one file.
func (in *Input) validate(kind Kind, creating bool, now time.Time) error {
	var v []Violation
	add := func(field, code string) { v = append(v, Violation{field, code}) }

	switch {
	case in.Description == "":
		add("description", "description.required")
	case utf8.RuneCountInString(in.Description) > 500:
		add("description", "description.length")
	}
	switch kind {
	case Expense:
		if in.Date == nil {
			add("date", "date.required")
		} else if in.Date.Format(time.DateOnly) > now.Format(time.DateOnly) {
			// Calendar days, both in Swedish time: comparing the date's
			// midnight with the clock refused today's date just after midnight.
			add("date", "date.future")
		}
	case Invoice:
		if in.InvoiceNumber == "" {
			add("invoice_number", "invoice_number.required")
		}
		if in.Date != nil && in.DueDate != nil && in.DueDate.Before(*in.Date) {
			add("due_date", "due_date.before_invoice_date")
		}
	}
	if len(in.Parts) == 0 {
		add("parts", "parts.required")
	}
	for i, p := range in.Parts {
		field := func(name string) string { return fmt.Sprintf("parts[%d].%s", i, name) }
		if p.CostCentre == "" {
			add(field("cost_centre"), "cost_centre.required")
		}
		if p.SecondaryCostCentre == "" {
			add(field("secondary_cost_centre"), "secondary_cost_centre.required")
		}
		if p.BudgetLine == "" {
			add(field("budget_line"), "budget_line.required")
		}
		switch {
		case p.AmountOre <= 0:
			add(field("amount_ore"), "amount.positive")
		case p.AmountOre > maxAmountOre:
			add(field("amount_ore"), "amount.too_large")
		}
	}
	if creating && len(in.UploadIDs) == 0 {
		add("files", "files.required")
	}
	if len(v) > 0 {
		return &InvalidInput{Violations: v}
	}
	return nil
}

func pgDate(t *time.Time) pgtype.Date {
	if t == nil {
		return pgtype.Date{}
	}
	return pgtype.Date{Time: *t, Valid: true}
}

// Create submits a new claim owned by the viewer and returns its number.
func (s *Store) Create(ctx context.Context, v Viewer, kind Kind, in Input) (int64, error) {
	in.normalise()
	if err := in.validate(kind, true, time.Now().In(stockholm)); err != nil {
		return 0, err
	}
	var number int64
	err := pgx.BeginFunc(ctx, s.pool, func(tx pgx.Tx) error {
		q := db.New(tx)
		actor, err := q.GetActor(ctx, v.Username)
		if err != nil {
			return fmt.Errorf("actor: %w", err)
		}
		params := db.InsertClaimParams{Description: in.Description, CreatedDate: today(), OwnerID: actor.ProfileID}
		if kind == Expense {
			number, err = q.InsertExpenseData(ctx, pgDate(in.Date))
			params.ExpenseDataID = pgInt8(number)
		} else {
			number, err = q.InsertInvoiceData(ctx, db.InsertInvoiceDataParams{
				InvoiceDate: pgDate(in.Date), InvoiceNumber: in.InvoiceNumber, DueDate: pgDate(in.DueDate),
			})
			params.InvoiceDataID = pgInt8(number)
		}
		if err != nil {
			return err
		}
		claimID, err := q.InsertClaim(ctx, params)
		if err != nil {
			return err
		}
		if err := insertParts(ctx, q, claimID, in.Parts); err != nil {
			return err
		}
		_, err = attachUploads(ctx, q, claimID, v.Username, in.UploadIDs)
		return err
	})
	return number, err
}

// Update edits a claim the viewer owns and has not been paid. As in
// Cashflow 3, changing the parts or files voids the receipt's confirmation,
// and editing an expense clears its flag. Unlike Cashflow 3, parts are only
// replaced when they changed, so fixing a typo keeps the attestations.
func (s *Store) Update(ctx context.Context, v Viewer, kind Kind, number int64, in Input) error {
	in.normalise()
	if err := in.validate(kind, false, time.Now().In(stockholm)); err != nil {
		return err
	}
	return s.withClaim(ctx, v, kind, number, func(c *change) error {
		if err := v.CanEdit(c.state); err != nil {
			return err
		}
		q, id := c.q, c.claim.ID
		if err := q.UpdateClaimDescription(ctx, db.UpdateClaimDescriptionParams{ID: id, Description: in.Description}); err != nil {
			return err
		}
		if kind == Expense {
			if err := q.UpdateExpenseDate(ctx, db.UpdateExpenseDateParams{ID: c.claim.ExpenseDataID.Int64, ExpenseDate: pgDate(in.Date)}); err != nil {
				return err
			}
		} else if err := q.UpdateInvoiceData(ctx, db.UpdateInvoiceDataParams{
			ID: c.claim.InvoiceDataID.Int64, InvoiceDate: pgDate(in.Date), InvoiceNumber: in.InvoiceNumber, DueDate: pgDate(in.DueDate),
		}); err != nil {
			return err
		}

		current, err := q.ListPartsForEdit(ctx, id)
		if err != nil {
			return err
		}
		partsChanged := !slices.EqualFunc(current, in.Parts, func(a db.ListPartsForEditRow, b PartInput) bool {
			return a.CostCentre == b.CostCentre && a.SecondaryCostCentre == b.SecondaryCostCentre &&
				a.BudgetLine == b.BudgetLine && a.AmountOre == b.AmountOre
		})
		if partsChanged {
			if err := q.DeleteClaimParts(ctx, id); err != nil {
				return err
			}
			if err := insertParts(ctx, q, id, in.Parts); err != nil {
				return err
			}
		}

		removed, err := q.DeleteFiles(ctx, db.DeleteFilesParams{ClaimID: id, Ids: in.RemoveFileIDs})
		if err != nil {
			return err
		}
		added, err := attachUploads(ctx, q, id, v.Username, in.UploadIDs)
		if err != nil {
			return err
		}
		if kind == Expense && (partsChanged || removed > 0 || added > 0) {
			return q.ResetConfirmation(ctx, c.claim.ExpenseDataID.Int64)
		}
		return nil
	})
}

func insertParts(ctx context.Context, q *db.Queries, claimID int64, parts []PartInput) error {
	for _, p := range parts {
		if err := q.InsertPart(ctx, db.InsertPartParams{
			ClaimID: claimID, CostCentre: p.CostCentre, SecondaryCostCentre: p.SecondaryCostCentre,
			BudgetLine: p.BudgetLine, AmountOre: p.AmountOre,
		}); err != nil {
			return fmt.Errorf("part: %w", err)
		}
	}
	return nil
}

// attachUploads moves the viewer's uploads onto a claim. An unknown, someone
// else's or already attached upload is an error, so files are never lost.
func attachUploads(ctx context.Context, q *db.Queries, claimID int64, username string, ids []string) (int, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	ids = slices.Compact(slices.Sorted(slices.Values(ids)))
	uploads, err := q.TakeUploads(ctx, db.TakeUploadsParams{Ids: ids, Uploader: username})
	if err != nil {
		return 0, err
	}
	if len(uploads) != len(ids) {
		return 0, &InvalidInput{Violations: []Violation{{"files", "files.unknown_upload"}}}
	}
	for _, u := range uploads {
		if err := q.InsertFile(ctx, db.InsertFileParams{ClaimID: claimID, File: u.StorageKey}); err != nil {
			return 0, err
		}
	}
	return len(uploads), nil
}
