// Package claims reads expenses and invoices ("claims") from Cashflow 3's
// tables, and holds the rules for who sees what and which work queue a claim
// is in. They port Cashflow 3's ClaimQuerySet (core/models.py); keep the two
// in step until the cutover.
package claims

import (
	"errors"
	"strconv"
	"time"

	"github.com/datasektionen/cashflow/server/internal/perm"
)

var (
	ErrNotFound       = errors.New("claim not found")
	ErrForbiddenQueue = errors.New("queue not available to this user")
)

type Kind string

const (
	Expense Kind = "expense"
	Invoice Kind = "invoice"
)

type Queue string

const (
	QueueAttest  Queue = "attest"
	QueueConfirm Queue = "confirm"
	QueueAccount Queue = "account"
	QueuePay     Queue = "pay"
)

// Queues in the order the sidebar shows them.
var Queues = []Queue{QueueAttest, QueueConfirm, QueueAccount, QueuePay}

type Sort string

const (
	SortDate        Sort = "date"
	SortAmount      Sort = "amount"
	SortDescription Sort = "description"
	SortOwner       Sort = "owner"
	SortCreated     Sort = "created"
)

// Viewer is who is asking, with their resolved permissions.
type Viewer struct {
	Username string
	Perms    perm.Set
}

// MaySeeQueue reports whether the queue exists for the viewer at all.
func (v Viewer) MaySeeQueue(q Queue) bool {
	switch q {
	case QueueAttest:
		return v.Perms.MaySeeAttestQueue()
	case QueueConfirm:
		return v.Perms.MaySeeConfirmQueue()
	case QueueAccount:
		return v.Perms.MaySeeAccountQueue()
	case QueuePay:
		return v.Perms.MaySeePayQueue()
	}
	return false
}

type Person struct {
	Username string
	Name     string
}

// Summary is a claim as lists show it.
type Summary struct {
	ID           int64 // core_claim.id, internal
	Kind         Kind
	Number       int64 // public id: expense_data.id or invoice_data.id
	Description  string
	Owner        Person
	AmountOre    int64
	Date         *time.Time // expense date, else invoice date, else payment date
	CreatedDate  time.Time
	CostCentres  []string
	Attested     bool // every part attested
	Confirmed    bool // expenses only
	Paid         bool
	Flagged      bool // expenses only
	Verification string
}

// PaymentTag is the bank reference of a payment, as Cashflow 3's
// PAYMENT_TAG_PREFIX + id.
func PaymentTag(paymentID int64) string {
	return "Data" + strconv.FormatInt(paymentID, 10)
}

// Stage numbers match cashflow.claim.v1.Stage.
type Stage int

const (
	StageSubmitted Stage = iota + 1
	StageAttested
	StageConfirmed
	StagePaid
	StageAccounted
)

// Stage is the furthest step reached in order. Expenses go submitted →
// attested → confirmed → paid → accounted; invoices skip confirmation. An
// expense confirmed before it is attested is still at "submitted".
func (s Summary) Stage() Stage {
	switch {
	case s.Verification != "":
		return StageAccounted
	case s.Paid:
		return StagePaid
	case !s.Attested:
		return StageSubmitted
	case s.Kind == Expense && s.Confirmed:
		return StageConfirmed
	default:
		return StageAttested
	}
}

// Filter narrows a claims list.
type Filter struct {
	Mine       bool
	Queue      Queue
	Kind       Kind
	Query      string
	CostCentre string
	// Accounted keeps only claims with a voucher, optionally in one series.
	Accounted     bool
	VoucherSeries string
	Advanced      Advanced
	Sort          Sort
	Descending    bool
	Page          int // 1-based
	PageSize      int

	// Exact lookups, for the detail page and file access.
	ID     int64
	Number int64
}

// Advanced holds the filter panel's filters; zero values do not filter.
type Advanced struct {
	SecondaryCostCentre string
	BudgetLine          string
	From, To            *time.Time
	Owner               string // username
	InvoiceNumber       string
	Verification        string // exact voucher number, e.g. "E12"
	PaymentID           int64
	// Tristates: nil does not filter.
	Attested, Confirmed, Paid, Accounted, Flagged *bool
}

const (
	DefaultPageSize = 25
	MaxPageSize     = 100
)

// normalise fills in defaults: queues list the oldest first (they are worked
// through in order), other lists the newest first.
func (f Filter) normalise() Filter {
	if f.Page < 1 {
		f.Page = 1
	}
	if f.PageSize < 1 {
		f.PageSize = DefaultPageSize
	}
	f.PageSize = min(f.PageSize, MaxPageSize)
	if f.Sort == "" {
		f.Sort = SortDate
		f.Descending = f.Queue == ""
	}
	return f
}
