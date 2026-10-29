package claims

import (
	"errors"
	"slices"
	"testing"

	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

func TestRules(t *testing.T) {
	attester := viewer("cecilia", map[string]hive.Grant{perm.Attest: scoped("ada")})
	treasurer := viewer("kassor", map[string]hive.Grant{perm.Pay: all, perm.Confirm: all, perm.Attest: all})
	expense := State{Kind: Expense, Owner: "anna", Parts: []PartState{{ID: 1, CostCentre: "Ada"}, {ID: 2, CostCentre: "DSys"}}}

	check := func(name string, got, want error) {
		t.Helper()
		if !errors.Is(got, want) {
			t.Errorf("%s: got %v, want %v", name, got, want)
		}
	}

	// Attesting.
	check("attest own cost centre", attester.CanAttest(expense, expense.Parts[0]), nil)
	check("attest other cost centre", attester.CanAttest(expense, expense.Parts[1]), ErrNotPermitted)
	own := expense
	own.Owner = "cecilia"
	check("attest own expense", attester.CanAttest(own, own.Parts[0]), ErrOwnExpense)
	ownInvoice := own
	ownInvoice.Kind = Invoice
	check("attest own invoice", attester.CanAttest(ownInvoice, ownInvoice.Parts[0]), nil)
	flagged := expense
	flagged.Flagged = true
	check("attest flagged", attester.CanAttest(flagged, flagged.Parts[0]), ErrFlagged)
	check("unattest unattested", attester.CanUnattest(expense, expense.Parts[0]), ErrNotAttested)

	// Confirming and flagging.
	check("confirm without permission", attester.CanConfirm(expense), ErrNotPermitted)
	check("confirm", treasurer.CanConfirm(expense), nil)
	check("confirm flagged", treasurer.CanConfirm(flagged), ErrFlagged)
	check("confirm invoice", treasurer.CanConfirm(ownInvoice), ErrNotExpense)
	check("flag", attester.CanSetFlag(expense, true), nil)
	check("flag twice", attester.CanSetFlag(flagged, true), ErrFlagUnchanged)
	check("flag without permission", viewer("nobody", nil).CanSetFlag(expense, true), ErrNotPermitted)

	// Paying invoices.
	invoice := State{Kind: Invoice, Owner: "anna", Parts: []PartState{{ID: 1, CostCentre: "Ada", Attested: true}}}
	check("pay attested invoice", treasurer.CanPayInvoice(invoice), nil)
	invoice.Parts = append(invoice.Parts, PartState{ID: 2, CostCentre: "Ada"})
	check("pay partly attested", treasurer.CanPayInvoice(invoice), ErrNotFullyAttested)
	check("pay expense", treasurer.CanPayInvoice(expense), ErrNotInvoice)

	// Deleting and editing.
	check("owner deletes", viewer("anna", nil).CanDelete(expense), nil)
	check("stranger deletes", viewer("bertil", nil).CanDelete(expense), ErrNotPermitted)
	check("admin deletes", viewer("bertil", map[string]hive.Grant{perm.Delete: all}).CanDelete(expense), nil)
	paid := expense
	paid.Paid = true
	check("delete paid", viewer("anna", nil).CanDelete(paid), ErrAlreadyPaid)
	check("edit paid", viewer("anna", nil).CanEdit(paid), ErrAlreadyPaid)
	check("others edit", treasurer.CanEdit(expense), ErrNotPermitted)

	// Actions agree with the rules.
	a := attester.Actions(expense)
	if !slices.Equal(a.Attest, []int64{1}) || a.Confirm || !a.Flag || a.Unflag || a.Delete {
		t.Errorf("unexpected actions %+v", a)
	}
}
