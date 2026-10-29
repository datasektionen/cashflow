// Package perm holds Cashflow's permission rules on top of Hive permissions.
// It is a port of cashflow/dauth.py and core.models.Profile from Cashflow 3;
// keep the two in step until the cutover.
package perm

import (
	"github.com/datasektionen/cashflow/server/internal/hive"
)

// Hive permission ids for the "cashflow" system.
const (
	Accounting          = "accounting"
	Attest              = "attest"
	AttestFirmatecknare = "attest-firmatecknare"
	Confirm             = "confirm"
	Delete              = "delete"
	EditInvoice         = "edit-invoice"
	ManageFortnox       = "manage-fortnox"
	ModerateComments    = "moderate-comments"
	Pay                 = "pay"
	Unattest            = "unattest"
	ViewAccount         = "view-account"
	ViewAll             = "view-all"
	ViewAllPayments     = "view-all-payments"
	ViewExpenses        = "view-expenses"
)

// Set answers permission questions for one user.
type Set struct {
	Username string
	perms    hive.Permissions
}

func New(username string, perms hive.Permissions) Set {
	return Set{Username: username, perms: perms}
}

func (s Set) MayViewAll() bool {
	return s.perms.Has(ViewAll) || s.perms.Has(ViewExpenses)
}

func (s Set) MayViewAllPayments() bool { return s.perms.Has(ViewAllPayments) }

func (s Set) MayViewCostCentre(cc string) bool {
	return s.MayViewAll() || s.perms.HasScope(ViewExpenses, cc)
}

func (s Set) MayAttest(cc string) bool { return s.perms.HasScope(Attest, cc) }
func (s Set) MayAttestAll() bool       { return s.perms.Has(Attest) }
func (s Set) MayAttestSome() bool      { return s.perms.HasAny(Attest) }
func (s Set) MayUnattest() bool        { return s.perms.Has(Unattest) }

// MayConfirm also covers unconfirming, as in Cashflow 3.
func (s Set) MayConfirm() bool { return s.perms.Has(Confirm) }

func (s Set) MayAccount(cc string) bool { return s.perms.HasScope(Accounting, cc) }
func (s Set) MayAccountAll() bool       { return s.perms.Has(Accounting) }
func (s Set) MayAccountSome() bool      { return s.perms.HasAny(Accounting) }

// MayAccountClaim reports whether the user may account a claim with parts in
// the given cost centres: any one matching part is enough.
func (s Set) MayAccountClaim(costCentres []string) bool {
	if s.MayAccountAll() {
		return true
	}
	for _, cc := range costCentres {
		if s.MayAccount(cc) {
			return true
		}
	}
	return false
}

func (s Set) MayPay() bool              { return s.perms.Has(Pay) }
func (s Set) MayDelete() bool           { return s.perms.Has(Delete) }
func (s Set) MayEditInvoice() bool      { return s.perms.Has(EditInvoice) }
func (s Set) MayModerateComments() bool { return s.perms.Has(ModerateComments) }
func (s Set) MayManageFortnox() bool    { return s.perms.Has(ManageFortnox) }
func (s Set) MayFirmatecknare() bool    { return s.perms.HasAny(AttestFirmatecknare) }
func (s Set) MayViewAccount() bool      { return s.perms.HasAny(ViewAccount) }
func (s Set) MayFlag() bool             { return s.MayAttestSome() || s.MayPay() }

// IsAdmin reports whether the user sees the admin section at all.
func (s Set) IsAdmin() bool {
	return s.MayAttestSome() || s.MayPay() || s.MayConfirm() || s.MayAccountSome() || s.MayViewAll()
}

// Filter returns the cost centres in all that allowed accepts.
func Filter(all []string, allowed func(string) bool) []string {
	out := []string{}
	for _, cc := range all {
		if allowed(cc) {
			out = append(out, cc)
		}
	}
	return out
}
