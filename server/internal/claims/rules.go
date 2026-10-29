package claims

// The workflow rules, ported from Cashflow 3's Claim and ClaimPart methods
// (core/models.py) and the expense/invoice viewsets. Each rule returns nil
// when the viewer may take the action, or a *Problem saying why not. The
// same functions decide which buttons the frontend shows (Actions) and are
// checked again, on locked rows, when the action runs.

// Problem is a rule the action breaks. Code is stable; the frontend shows a
// translated message for it.
type Problem struct {
	Code string
	// Forbidden problems are about who the viewer is rather than the
	// claim's state; the API reports them as PermissionDenied.
	Forbidden bool
}

func (p *Problem) Error() string { return "claims: " + p.Code }

var (
	ErrNotPermitted     = &Problem{Code: "not_permitted", Forbidden: true}
	ErrOwnExpense       = &Problem{Code: "own_expense", Forbidden: true}
	ErrFlagged          = &Problem{Code: "flagged"}
	ErrAlreadyAttested  = &Problem{Code: "already_attested"}
	ErrNotAttested      = &Problem{Code: "not_attested"}
	ErrAlreadyConfirmed = &Problem{Code: "already_confirmed"}
	ErrNotConfirmed     = &Problem{Code: "not_confirmed"}
	ErrNotExpense       = &Problem{Code: "not_expense"}
	ErrNotInvoice       = &Problem{Code: "not_invoice"}
	ErrNotFullyAttested = &Problem{Code: "not_fully_attested"}
	ErrAlreadyPaid      = &Problem{Code: "already_paid"}
	ErrEmptyComment     = &Problem{Code: "empty_comment"}
	ErrPartNotOnClaim   = &Problem{Code: "part_not_on_claim"}
	ErrFlagUnchanged    = &Problem{Code: "flag_unchanged"}
	ErrNoExpenses       = &Problem{Code: "no_expenses"}
	ErrSeveralReceivers = &Problem{Code: "several_receivers"}
)

// State is what the rules look at.
type State struct {
	Kind      Kind
	Owner     string // username
	Flagged   bool
	Confirmed bool
	// Paid: reimbursed for expenses; paid_by or paid_at set for invoices.
	Paid  bool
	Parts []PartState
}

type PartState struct {
	ID         int64
	CostCentre string
	Attested   bool
}

func (s State) fullyAttested() bool {
	if len(s.Parts) == 0 {
		return false
	}
	for _, p := range s.Parts {
		if !p.Attested {
			return false
		}
	}
	return true
}

// CanAttest: ClaimPart.attest. Never one's own expense (one's own invoice is
// fine), never while flagged, only in cost centres one attests.
func (v Viewer) CanAttest(s State, p PartState) error {
	switch {
	case p.Attested:
		return ErrAlreadyAttested
	case !v.Perms.MayAttest(p.CostCentre):
		return ErrNotPermitted
	case s.Kind == Expense && s.Owner == v.Username:
		return ErrOwnExpense
	case s.Flagged:
		return ErrFlagged
	}
	return nil
}

// CanUnattest: ClaimPart.unattest, which checks the cost centre rather than
// the separate "unattest" permission.
func (v Viewer) CanUnattest(_ State, p PartState) error {
	switch {
	case !p.Attested:
		return ErrNotAttested
	case !v.Perms.MayAttest(p.CostCentre):
		return ErrNotPermitted
	}
	return nil
}

// CanConfirm: Claim.confirm. Only expenses have receipts to confirm.
func (v Viewer) CanConfirm(s State) error {
	switch {
	case s.Kind != Expense:
		return ErrNotExpense
	case !v.Perms.MayConfirm():
		return ErrNotPermitted
	case s.Confirmed:
		return ErrAlreadyConfirmed
	case s.Flagged:
		return ErrFlagged
	}
	return nil
}

// CanUnconfirm: Claim.unconfirm; unconfirming needs the confirm permission.
func (v Viewer) CanUnconfirm(s State) error {
	switch {
	case s.Kind != Expense:
		return ErrNotExpense
	case !v.Perms.MayConfirm():
		return ErrNotPermitted
	case !s.Confirmed:
		return ErrNotConfirmed
	}
	return nil
}

// CanSetFlag: the flag and unflag actions, for attesters and payers.
func (v Viewer) CanSetFlag(s State, flagged bool) error {
	switch {
	case s.Kind != Expense:
		return ErrNotExpense
	case !v.Perms.MayFlag():
		return ErrNotPermitted
	case s.Flagged == flagged:
		return ErrFlagUnchanged
	}
	return nil
}

// CanPayInvoice: the invoice pay action. Expenses are paid out in batches
// per person instead (payouts).
func (v Viewer) CanPayInvoice(s State) error {
	switch {
	case s.Kind != Invoice:
		return ErrNotInvoice
	case !v.Perms.MayPay():
		return ErrNotPermitted
	case s.Paid:
		return ErrAlreadyPaid
	case !s.fullyAttested():
		return ErrNotFullyAttested
	}
	return nil
}

// CanDelete: the owner or someone with the delete permission, until paid.
func (v Viewer) CanDelete(s State) error {
	switch {
	case s.Paid:
		return ErrAlreadyPaid
	case s.Owner != v.Username && !v.Perms.MayDelete():
		return ErrNotPermitted
	}
	return nil
}

// CanEdit: only the owner, until paid.
func (v Viewer) CanEdit(s State) error {
	switch {
	case s.Paid:
		return ErrAlreadyPaid
	case s.Owner != v.Username:
		return ErrNotPermitted
	}
	return nil
}

// Actions is what the viewer may do with a claim right now.
type Actions struct {
	Attest, Unattest   []int64 // part ids
	Confirm, Unconfirm bool
	Flag, Unflag       bool
	PayInvoice         bool
	Delete, Edit       bool
}

func (v Viewer) Actions(s State) Actions {
	ok := func(err error) bool { return err == nil }
	a := Actions{
		Confirm:    ok(v.CanConfirm(s)),
		Unconfirm:  ok(v.CanUnconfirm(s)),
		Flag:       ok(v.CanSetFlag(s, true)),
		Unflag:     ok(v.CanSetFlag(s, false)),
		PayInvoice: ok(v.CanPayInvoice(s)),
		Delete:     ok(v.CanDelete(s)),
		Edit:       ok(v.CanEdit(s)),
	}
	for _, p := range s.Parts {
		if ok(v.CanAttest(s, p)) {
			a.Attest = append(a.Attest, p.ID)
		}
		if ok(v.CanUnattest(s, p)) {
			a.Unattest = append(a.Unattest, p.ID)
		}
	}
	return a
}

// CanPayOut: an expense may join a payout when it is fully attested, its
// receipt confirmed, not yet paid and not flagged. Cashflow 3's payment
// endpoint only checked "not reimbursed"; the pay queue's rules are applied
// here too, so nothing unready can be paid by accident.
func (v Viewer) CanPayOut(s State) error {
	switch {
	case s.Kind != Expense:
		return ErrNotExpense
	case !v.Perms.MayPay():
		return ErrNotPermitted
	case s.Paid:
		return ErrAlreadyPaid
	case s.Flagged:
		return ErrFlagged
	case !s.fullyAttested():
		return ErrNotFullyAttested
	case !s.Confirmed:
		return ErrNotConfirmed
	}
	return nil
}
