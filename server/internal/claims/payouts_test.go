package claims

import (
	"context"
	"errors"
	"fmt"
	"testing"

	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

func TestPayouts(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	f.profile("kassor")
	treasurer := viewer("kassor", map[string]hive.Grant{perm.Pay: all})

	a1 := f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, parts: []partSpec{{"Ada", 10000, true}}})
	a2 := f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, parts: []partSpec{{"Ada", 2550, true}, {"DSys", 50, true}}})
	unready := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 999, true}}}) // not confirmed
	flagged := f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, flagged: true, parts: []partSpec{{"Ada", 777, true}}})
	b1 := f.add(claimSpec{kind: Expense, owner: "bertil", confirmed: true, parts: []partSpec{{"Ada", 50000, true}}})
	f.add(claimSpec{kind: Invoice, owner: "bertil", parts: []partSpec{{"Ada", 1, true}}}) // invoices are not payouts

	pending, err := s.PendingPayouts(ctx, treasurer)
	if err != nil {
		t.Fatal(err)
	}
	if len(pending) != 2 || pending[0].Receiver.Username != "bertil" || pending[0].TotalOre != 50000 ||
		pending[1].Receiver.Username != "anna" || pending[1].TotalOre != 12600 || len(pending[1].Expenses) != 3 {
		t.Fatalf("pending payouts, largest first, flagged listed but not counted: %+v", pending)
	}

	for name, numbers := range map[string][]int64{
		"nothing":       nil,
		"unconfirmed":   {a1, unready},
		"flagged":       {flagged},
		"two receivers": {a1, b1},
	} {
		if _, err := s.CreatePayout(ctx, treasurer, numbers); err == nil {
			t.Errorf("%s: payout should be refused", name)
		}
	}
	if _, err := s.CreatePayout(ctx, viewer("anna", nil), []int64{a1}); !errors.Is(err, ErrNotPermitted) {
		t.Errorf("only payers pay out: %v", err)
	}

	id, err := s.CreatePayout(ctx, treasurer, []int64{a2, a1, a1})
	if err != nil {
		t.Fatal(err)
	}
	for _, n := range []int64{a1, a2} {
		if c, _ := s.Get(ctx, treasurer, Expense, n); !c.Paid {
			t.Errorf("expense %d should be paid", n)
		}
		if got := f.comments(Expense, n); got[len(got)-1] != fmt.Sprintf("Betalade ut i betalning %d", id) {
			t.Errorf("payout comment %q", got)
		}
	}
	if len(f.emails()) != 2 {
		t.Errorf("each expense's owner is emailed, got %d emails", len(f.emails()))
	}
	if _, err := s.CreatePayout(ctx, treasurer, []int64{a1}); !errors.Is(err, ErrAlreadyPaid) {
		t.Errorf("paying out twice: %v", err)
	}

	payments, total, err := s.ListPayments(ctx, treasurer, fmt.Sprintf("Data%d", id), 1, 25)
	if err != nil || total != 1 || len(payments) != 1 || payments[0].TotalOre != 12600 || len(payments[0].Expenses) != 2 ||
		payments[0].Receiver.Username != "anna" || payments[0].Payer.Username != "kassor" {
		t.Errorf("payments %+v, total %d, %v", payments, total, err)
	}
	if _, _, err := s.ListPayments(ctx, viewer("anna", nil), "", 1, 25); !errors.Is(err, ErrNotPermitted) {
		t.Errorf("payments are for payers: %v", err)
	}
}
