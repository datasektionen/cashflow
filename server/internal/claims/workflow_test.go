package claims

import (
	"context"
	"encoding/json"
	"errors"
	"testing"

	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

// comments of a claim; expenses and invoices are numbered separately, so the kind is needed too.
func (f *fixtures) comments(kind Kind, number int64) []string {
	f.t.Helper()
	rows, err := f.pool.Query(context.Background(), `SELECT content FROM core_comment cm JOIN core_claim c ON c.id = cm.claim_id
		WHERE c.type = $1 AND COALESCE(c.expense_data_id, c.invoice_data_id) = $2 ORDER BY cm.id`, string(kind), number)
	if err != nil {
		f.t.Fatal(err)
	}
	var out []string
	for rows.Next() {
		var s string
		rows.Scan(&s)
		out = append(out, s)
	}
	return out
}

func (f *fixtures) emails() []Email {
	f.t.Helper()
	rows, err := f.pool.Query(context.Background(), `SELECT payload FROM cashflow4_outbox ORDER BY id`)
	if err != nil {
		f.t.Fatal(err)
	}
	var out []Email
	for rows.Next() {
		var raw []byte
		rows.Scan(&raw)
		var e Email
		json.Unmarshal(raw, &e)
		out = append(out, e)
	}
	return out
}

func TestAttestWritesCashflow3CommentAndEmailsOwner(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	n := f.add(claimSpec{kind: Expense, owner: "anna", description: "Pizza", parts: []partSpec{{"Ada", 12345, false}}})
	f.profile("cecilia")
	attester := viewer("cecilia", map[string]hive.Grant{perm.Attest: scoped("ada")})

	claim, _ := s.Get(ctx, attester, Expense, n)
	state, _ := s.State(ctx, attester, claim)
	partID := state.Parts[0].ID

	if err := s.SetAttested(ctx, attester, Expense, n, partID, true); err != nil {
		t.Fatal(err)
	}
	if got := f.comments(Expense, n); len(got) != 1 || got[0] != "Attesterar kvittodelen ```Pizza (: 123.45 kr)```" {
		t.Errorf("comments %q", got)
	}
	mails := f.emails()
	if len(mails) != 1 || mails[0].To != "anna@kth.se" || mails[0].Subject != "cecilia Testsson har lagt till en kommentar på ditt utlägg." {
		t.Fatalf("emails %+v", mails)
	}
	if after, _ := s.Get(ctx, attester, Expense, n); !after.Attested {
		t.Error("part should be attested")
	}

	// Attesting again breaks a rule; owners may comment, without an email to themselves.
	if err := s.SetAttested(ctx, attester, Expense, n, partID, true); !errors.Is(err, ErrAlreadyAttested) {
		t.Errorf("attest twice: %v", err)
	}
	if err := s.AddComment(ctx, viewer("anna", nil), Expense, n, "  Tack!  "); err != nil {
		t.Fatal(err)
	}
	if got := f.comments(Expense, n); got[len(got)-1] != "Tack!" || len(f.emails()) != 1 {
		t.Errorf("own comment should be stored trimmed and not emailed: %q, %d emails", got, len(f.emails()))
	}
	if err := s.AddComment(ctx, viewer("anna", nil), Expense, n, "   "); !errors.Is(err, ErrEmptyComment) {
		t.Errorf("empty comment: %v", err)
	}

	if err := s.SetAttested(ctx, attester, Expense, n, partID, false); err != nil {
		t.Fatal(err)
	}
	if got := f.comments(Expense, n); got[len(got)-1] != "Avattesterar kvittodelen ```Pizza (: 123.45 kr)```" {
		t.Errorf("unattest comment %q", got[len(got)-1])
	}
}

func TestConfirmFlagPayAndDelete(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	treasurer := viewer("kassor", map[string]hive.Grant{perm.Pay: all, perm.Confirm: all, perm.Attest: all})
	f.profile("kassor")

	exp := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, true}}})
	if err := s.SetFlagged(ctx, treasurer, exp, true); err != nil {
		t.Fatal(err)
	}
	if err := s.SetConfirmed(ctx, treasurer, exp, true); !errors.Is(err, ErrFlagged) {
		t.Errorf("confirming a flagged expense: %v", err)
	}
	if err := s.SetFlagged(ctx, treasurer, exp, false); err != nil {
		t.Fatal(err)
	}
	if err := s.SetConfirmed(ctx, treasurer, exp, true); err != nil {
		t.Fatal(err)
	}
	if got := f.comments(Expense, exp); got[len(got)-1] != "Jag har bekräftat kvittots giltighet." {
		t.Errorf("confirm comment %q", got)
	}
	if c, _ := s.Get(ctx, treasurer, Expense, exp); !c.Confirmed {
		t.Error("should be confirmed")
	}

	inv := f.add(claimSpec{kind: Invoice, owner: "anna", description: "Hyra", parts: []partSpec{{"Ada", 100, true}}})
	if err := s.PayInvoice(ctx, treasurer, inv); err != nil {
		t.Fatal(err)
	}
	if got := f.comments(Invoice, inv); got[0] != "Betalade fakturan ```Hyra```" {
		t.Errorf("pay comment %q", got)
	}
	if err := s.PayInvoice(ctx, treasurer, inv); !errors.Is(err, ErrAlreadyPaid) {
		t.Errorf("paying twice: %v", err)
	}
	if err := s.Delete(ctx, viewer("anna", nil), Invoice, inv); !errors.Is(err, ErrAlreadyPaid) {
		t.Errorf("deleting a paid invoice: %v", err)
	}

	// Deleting removes the claim and everything under it.
	if err := s.Delete(ctx, viewer("bertil", nil), Expense, exp); !errors.Is(err, ErrNotFound) {
		t.Errorf("a stranger cannot even see it: %v", err)
	}
	if err := s.Delete(ctx, viewer("anna", nil), Expense, exp); err != nil {
		t.Fatal(err)
	}
	if _, err := s.Get(ctx, treasurer, Expense, exp); !errors.Is(err, ErrNotFound) {
		t.Errorf("deleted claim still there: %v", err)
	}
	var left int
	f.pool.QueryRow(ctx, `SELECT (SELECT count(*) FROM core_claimpart) + (SELECT count(*) FROM expenses_expensedata)
		+ (SELECT count(*) FROM core_comment cm WHERE NOT EXISTS (SELECT 1 FROM core_claim c WHERE c.id = cm.claim_id))`).Scan(&left)
	if left != 1 { // the invoice's part
		t.Errorf("%d rows left behind", left)
	}
}
