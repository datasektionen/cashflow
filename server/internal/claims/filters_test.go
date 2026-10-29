package claims

import (
	"context"
	"fmt"
	"slices"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"

	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

func TestAdvancedFilters(t *testing.T) {
	s, f := testStore(t)
	viewAll := viewer("admin", map[string]hive.Grant{perm.ViewAll: all})
	day := func(d int) time.Time { return time.Date(2026, 9, d, 0, 0, 0, 0, time.UTC) }
	yes, no := true, false

	fika := f.add(claimSpec{kind: Expense, owner: "anna", date: day(1), parts: []partSpec{{"Ada", 100, true}}, confirmed: true, paid: true, verification: "E12"})
	spel := f.add(claimSpec{kind: Expense, owner: "bertil", date: day(10), parts: []partSpec{{"Ada", 200, false}}, flagged: true})
	hyra := f.add(claimSpec{kind: Invoice, owner: "anna", date: day(20), parts: []partSpec{{"Mottagningen", 300, true}}})
	f.pool.Exec(context.Background(), `UPDATE core_claimpart SET secondary_cost_centre = 'Kärnverksamhet', budget_line = 'Fika' WHERE amount = 1`)
	f.pool.Exec(context.Background(), `UPDATE invoices_invoicedata SET invoice_number = 'INV-2026-77'`)
	var paymentID int64
	f.pool.QueryRow(context.Background(), `SELECT reimbursement_id FROM expenses_expensedata WHERE id = $1`, fika).Scan(&paymentID)

	e, i := func(n int64) string { return fmt.Sprintf("e%d", n) }, func(n int64) string { return fmt.Sprintf("i%d", n) }
	from, to := day(5), day(15)
	for name, tc := range map[string]struct {
		a    Advanced
		want []string
	}{
		"secondary, any case":  {Advanced{SecondaryCostCentre: "kärnverksamhet"}, []string{e(fika)}},
		"budget line":          {Advanced{BudgetLine: "FIKA"}, []string{e(fika)}},
		"date range inclusive": {Advanced{From: &from, To: &to}, []string{e(spel)}},
		"owner":                {Advanced{Owner: "anna"}, []string{i(hyra), e(fika)}},
		"invoice number part":  {Advanced{InvoiceNumber: "2026-77"}, []string{i(hyra)}},
		"verification":         {Advanced{Verification: "e12"}, []string{e(fika)}},
		"payment":              {Advanced{PaymentID: paymentID}, []string{e(fika)}},
		"attested":             {Advanced{Attested: &yes}, []string{i(hyra), e(fika)}},
		"not attested":         {Advanced{Attested: &no}, []string{e(spel)}},
		"flagged":              {Advanced{Flagged: &yes}, []string{e(spel)}},
		"paid and accounted":   {Advanced{Paid: &yes, Accounted: &yes}, []string{e(fika)}},
		"unconfirmed":          {Advanced{Confirmed: &no}, []string{i(hyra), e(spel)}},
	} {
		got := numbers(t, s, viewAll, Filter{Advanced: tc.a})
		slices.Sort(got)
		slices.Sort(tc.want)
		if !slices.Equal(got, tc.want) {
			t.Errorf("%s: got %v, want %v", name, got, tc.want)
		}
	}

	// Filters never widen what the viewer sees.
	bertil := viewer("bertil", nil)
	if got := numbers(t, s, bertil, Filter{Advanced: Advanced{Owner: "anna"}}); len(got) != 0 {
		t.Errorf("bertil sees anna's claims: %v", got)
	}
}

func TestBreakdown(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	kassor := viewer("kassor", map[string]hive.Grant{perm.Attest: all, perm.Pay: all})
	f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, false}, {"DSys", 100, false}}})
	f.add(claimSpec{kind: Expense, owner: "bertil", parts: []partSpec{{"Ada", 100, false}}})
	f.add(claimSpec{kind: Invoice, owner: "anna", parts: []partSpec{{"Ada", 100, true}}})
	f.add(claimSpec{kind: Invoice, owner: "anna", parts: []partSpec{{"DSys", 100, true}}})

	attest, err := s.Breakdown(ctx, kassor, QueueAttest)
	if err != nil || !slices.Equal(attest, []Count{{"Ada", "Ada", 2}, {"DSys", "DSys", 1}}) {
		t.Errorf("attest: %+v %v", attest, err)
	}
	pay, err := s.Breakdown(ctx, kassor, QueuePay)
	if err != nil || !slices.Equal(pay, []Count{{"anna", "anna Testsson", 2}}) {
		t.Errorf("pay: %+v %v", pay, err)
	}
	if _, err := s.Breakdown(ctx, viewer("nobody", nil), QueuePay); err != ErrForbiddenQueue {
		t.Errorf("forbidden queue: %v", err)
	}
}

func TestStatsQueries(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	day := func(m time.Month, d int) time.Time { return time.Date(2026, m, d, 0, 0, 0, 0, time.UTC) }
	f.add(claimSpec{kind: Expense, owner: "anna", date: day(1, 5), parts: []partSpec{{"Ada", 10000, false}, {"Ada", 500, false}}})
	// 10 000 kr or more: counts, but not towards the leaderboard total.
	f.add(claimSpec{kind: Expense, owner: "anna", date: day(1, 9), parts: []partSpec{{"Ada", 1_000_000, false}}})
	f.add(claimSpec{kind: Expense, owner: "bertil", date: day(3, 1), parts: []partSpec{{"Ada", 20000, false}}})
	f.add(claimSpec{kind: Invoice, owner: "bertil", date: day(3, 2), parts: []partSpec{{"Ada", 99900, false}}})
	f.add(claimSpec{kind: Expense, owner: "cecilia", date: time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC), parts: []partSpec{{"Ada", 1, false}}})

	pg := func(t time.Time) pgtype.Date { return pgtype.Date{Time: t, Valid: true} }
	months, err := s.Queries.MonthlyStats(ctx, db.MonthlyStatsParams{FromDate: pg(day(1, 1)), ToDate: pg(time.Date(2027, 1, 1, 0, 0, 0, 0, time.UTC))})
	if err != nil {
		t.Fatal(err)
	}
	slices.SortFunc(months, func(a, b db.MonthlyStatsRow) int { return int(a.Month-b.Month)*10 + len(a.Kind) - len(b.Kind) })
	want := []db.MonthlyStatsRow{
		{Kind: "expense", Month: 1, Claims: 2, TotalOre: 1_010_500},
		{Kind: "expense", Month: 3, Claims: 1, TotalOre: 20000},
		{Kind: "invoice", Month: 3, Claims: 1, TotalOre: 99900},
	}
	if !slices.Equal(months, want) {
		t.Errorf("months\n got %+v\nwant %+v", months, want)
	}

	owners, err := s.Queries.ExpenseTotalsByOwner(ctx, pg(day(1, 1)))
	if err != nil {
		t.Fatal(err)
	}
	slices.SortFunc(owners, func(a, b db.ExpenseTotalsByOwnerRow) int { return len(a.Username) - len(b.Username) })
	wantOwners := []db.ExpenseTotalsByOwnerRow{
		{Username: "anna", Name: "anna Testsson", CappedTotalOre: 10500, TotalOre: 1_010_500, Expenses: 2},
		{Username: "bertil", Name: "bertil Testsson", CappedTotalOre: 20000, TotalOre: 20000, Expenses: 1},
	}
	if !slices.Equal(owners, wantOwners) {
		t.Errorf("owners\n got %+v\nwant %+v", owners, wantOwners)
	}
}
