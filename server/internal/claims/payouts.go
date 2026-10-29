package claims

import (
	"context"
	"fmt"
	"slices"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"

	"github.com/datasektionen/cashflow/server/internal/database/db"
)

type BankDetails struct {
	ClearingNumber string
	Account        string
	BankName       string
}

// PendingPayout is one person's expenses that wait in the pay queue.
type PendingPayout struct {
	Receiver Person
	Bank     BankDetails
	Expenses []Summary
	// TotalOre counts only the expenses that can be paid out now (not flagged).
	TotalOre int64
}

// PendingPayouts groups the expenses in the viewer's pay queue by owner,
// largest total first, as Cashflow 3's pending payments.
func (s *Store) PendingPayouts(ctx context.Context, v Viewer) ([]PendingPayout, error) {
	if !v.MaySeeQueue(QueuePay) {
		return nil, ErrForbiddenQueue
	}
	var expenses []Summary
	for page := 1; ; page++ {
		list, total, err := s.List(ctx, v, Filter{Queue: QueuePay, Kind: Expense, Sort: SortDate, Page: page, PageSize: MaxPageSize})
		if err != nil {
			return nil, err
		}
		expenses = append(expenses, list...)
		if page*MaxPageSize >= total {
			break
		}
	}

	byOwner := map[string]*PendingPayout{}
	var order []string
	for _, e := range expenses {
		p, ok := byOwner[e.Owner.Username]
		if !ok {
			user, err := s.Queries.GetUser(ctx, e.Owner.Username)
			if err != nil {
				return nil, fmt.Errorf("receiver %s: %w", e.Owner.Username, err)
			}
			p = &PendingPayout{
				Receiver: e.Owner,
				Bank:     BankDetails{ClearingNumber: user.SortingNumber, Account: user.BankAccount, BankName: user.BankName},
			}
			byOwner[e.Owner.Username] = p
			order = append(order, e.Owner.Username)
		}
		p.Expenses = append(p.Expenses, e)
		if !e.Flagged {
			p.TotalOre += e.AmountOre
		}
	}
	out := make([]PendingPayout, 0, len(order))
	for _, username := range order {
		out = append(out, *byOwner[username])
	}
	slices.SortStableFunc(out, func(a, b PendingPayout) int { return int(b.TotalOre - a.TotalOre) })
	return out, nil
}

// Payment is a payout: one bank transfer covering one person's expenses.
type Payment struct {
	ID       int64
	Tag      string
	Date     time.Time
	Payer    Person
	Receiver Person
	TotalOre int64
	Expenses []int64 // expense numbers
}

// CreatePayout records that the viewer paid out the given expenses, all of
// one person's, in one transfer. Each expense gets Cashflow 3's "Betalade ut
// i betalning N" comment, which also emails its owner.
func (s *Store) CreatePayout(ctx context.Context, v Viewer, numbers []int64) (int64, error) {
	if len(numbers) == 0 {
		return 0, ErrNoExpenses
	}
	if !v.Perms.MayPay() {
		return 0, ErrNotPermitted
	}
	slices.Sort(numbers)
	numbers = slices.Compact(numbers)

	summaries := make([]Summary, 0, len(numbers))
	for _, n := range numbers {
		summary, err := s.Get(ctx, v, Expense, n)
		if err != nil {
			return 0, err
		}
		summaries = append(summaries, summary)
	}

	var paymentID int64
	err := pgx.BeginFunc(ctx, s.pool, func(tx pgx.Tx) error {
		q := db.New(tx)
		changes := make([]*change, 0, len(summaries))
		for _, summary := range summaries {
			c, err := lock(ctx, q, v, summary)
			if err != nil {
				return err
			}
			if err := v.CanPayOut(c.state); err != nil {
				return err
			}
			if len(changes) > 0 && c.claim.OwnerID != changes[0].claim.OwnerID {
				return ErrSeveralReceivers
			}
			changes = append(changes, c)
		}

		first := changes[0]
		id, err := q.InsertPayment(ctx, db.InsertPaymentParams{OnDate: today(), PayerID: first.actor.ProfileID, ReceiverID: first.claim.OwnerID})
		if err != nil {
			return fmt.Errorf("payment: %w", err)
		}
		paymentID = id
		for _, c := range changes {
			if err := q.SetReimbursement(ctx, db.SetReimbursementParams{ID: c.claim.ExpenseDataID.Int64, PaymentID: pgInt8(id)}); err != nil {
				return err
			}
			if err := s.comment(ctx, c, fmt.Sprintf("Betalade ut i betalning %d", id)); err != nil {
				return err
			}
		}
		return nil
	})
	return paymentID, err
}

// MaySeePayments: payers and view-all admins, as Cashflow 3's payments list,
// plus anyone holding view-all-payments.
func (v Viewer) MaySeePayments() bool {
	return v.Perms.MayPay() || v.Perms.MayViewAll() || v.Perms.MayViewAllPayments()
}

// ListPayments returns a page of payments, newest first, optionally only
// those whose tag contains the query (e.g. "Data12").
func (s *Store) ListPayments(ctx context.Context, v Viewer, tagQuery string, page, pageSize int) ([]Payment, int, error) {
	if !v.MaySeePayments() {
		return nil, 0, ErrNotPermitted
	}
	f := Filter{Page: page, PageSize: pageSize}.normalise()
	rows, err := s.Queries.ListPayments(ctx, db.ListPaymentsParams{
		Tag: strings.TrimSpace(tagQuery), Lim: int32(f.PageSize), Off: int32((f.Page - 1) * f.PageSize),
	})
	if err != nil {
		return nil, 0, err
	}
	total := 0
	payments := make([]Payment, 0, len(rows))
	for _, r := range rows {
		total = int(r.TotalCount)
		p := Payment{
			ID: r.ID, Tag: PaymentTag(r.ID), Date: r.Date.Time,
			Payer:    Person{Username: r.PayerUsername, Name: r.PayerName},
			Receiver: Person{Username: r.ReceiverUsername, Name: r.ReceiverName},
			TotalOre: r.TotalOre,
		}
		if p.Expenses, err = s.Queries.ListPaymentExpenses(ctx, pgInt8(r.ID)); err != nil {
			return nil, 0, err
		}
		payments = append(payments, p)
	}
	return payments, total, nil
}
