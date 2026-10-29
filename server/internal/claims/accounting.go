package claims

import (
	"context"
	"errors"
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/datasektionen/cashflow/server/internal/budget"
	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/fortnox"
)

// Accounting ports Claim.account (core/models.py): a claim is accounted
// either by booking a voucher in Fortnox or by recording the number of a
// voucher someone already booked. Cashflow 3's settings decide the rest.
const (
	ExpenseCreditAccount = 2820 // skulder till medlemmar
	InvoiceCreditAccount = 2440 // leverantörsskulder
	ExpenseSeries        = "E"
	InvoiceSeries        = "U"
)

var (
	ErrFortnoxDisabled     = &Problem{Code: "fortnox_disabled"}
	ErrFortnoxNotConnected = &Problem{Code: "fortnox_not_connected"}
	// ErrFortnoxRecordMissing: the claim has a voucher number Fortnox does
	// not know.
	ErrFortnoxRecordMissing = &Problem{Code: "fortnox_record_missing"}
)

// VoucherExistsProblem: Fortnox already has a voucher for the claim that
// Cashflow never recorded (Cashflow 3's CashflowVerificationMissing), e.g.
// after a crash right after booking. Voucher says which, so it can be
// recorded instead of booked twice.
func VoucherExistsProblem(voucher string) *Problem {
	return &Problem{Code: "voucher_exists", Detail: voucher}
}

// Series is the voucher series claims of the kind are booked in.
func Series(kind Kind) string {
	if kind == Invoice {
		return InvoiceSeries
	}
	return ExpenseSeries
}

func CreditAccount(kind Kind) int {
	if kind == Invoice {
		return InvoiceCreditAccount
	}
	return ExpenseCreditAccount
}

// VoucherDescription is FORTNOX_DESCRIPTION_FORMAT: the claim number in
// brackets lets anyone in Fortnox find the claim, and Cashflow find the voucher.
func VoucherDescription(number int64, description string) string {
	return fmt.Sprintf("(%d) %s", number, description)
}

// AccountingInput is either an existing voucher number or rows to book.
type AccountingInput struct {
	VoucherNumber string
	Rows          []fortnox.VoucherRow
}

var voucherNumberPattern = regexp.MustCompile(`^[A-Z][0-9]+$`)

const maxVoucherRowOre = 1_000_000_000 - 1

// validate checks the rows against each other, the claim's total and
// Fortnox's chart of accounts and cost centres.
func (in AccountingInput) validate(totalOre int64, accounts []fortnox.Account, costCentres []fortnox.CostCentre) error {
	var v []Violation
	add := func(field, code string) { v = append(v, Violation{field, code}) }
	if len(in.Rows) == 0 {
		return &InvalidInput{Violations: []Violation{{"rows", "rows.required"}}}
	}
	knownAccount := map[int]bool{}
	for _, a := range accounts {
		knownAccount[a.Number] = true
	}
	knownCostCentre := map[string]bool{}
	for _, cc := range costCentres {
		knownCostCentre[cc.Code] = true
	}
	var debit, credit int64
	for i, r := range in.Rows {
		field := func(name string) string { return fmt.Sprintf("rows[%d].%s", i, name) }
		switch {
		case r.Account < 1000 || r.Account > 9999:
			add(field("account"), "account.required")
		case !knownAccount[r.Account]:
			add(field("account"), "account.unknown")
		}
		if r.CostCentre != "" && !knownCostCentre[r.CostCentre] {
			add(field("cost_centre"), "cost_centre.unknown")
		}
		switch {
		case r.Debit < 0 || r.Credit < 0 || (r.Debit > 0) == (r.Credit > 0):
			add(field("amount"), "amount.one_side")
		case r.Debit > maxVoucherRowOre || r.Credit > maxVoucherRowOre:
			add(field("amount"), "amount.too_large")
		}
		debit += int64(r.Debit)
		credit += int64(r.Credit)
	}
	if len(v) == 0 {
		switch {
		case debit != credit:
			add("rows", "rows.unbalanced")
		case debit != totalOre:
			add("rows", "rows.total_mismatch")
		}
	}
	if len(v) > 0 {
		return &InvalidInput{Violations: v}
	}
	return nil
}

// Account accounts a claim and returns its voucher number. Booking in
// Fortnox happens with the claim locked, so two accountants cannot book it
// twice; Fortnox is asked first whether it already has a voucher for the
// claim.
func (s *Store) Account(ctx context.Context, v Viewer, kind Kind, number int64, in AccountingInput, fx *fortnox.Client) (string, error) {
	in.VoucherNumber = strings.ToUpper(strings.TrimSpace(in.VoucherNumber))
	switch {
	case in.VoucherNumber != "" && len(in.Rows) > 0:
		return "", &InvalidInput{Violations: []Violation{{"voucher_number", "voucher_number.with_rows"}}}
	case in.VoucherNumber != "" && !voucherNumberPattern.MatchString(in.VoucherNumber):
		return "", &InvalidInput{Violations: []Violation{{"voucher_number", "voucher_number.format"}}}
	case in.VoucherNumber == "" && !fx.Enabled():
		return "", ErrFortnoxDisabled
	}

	var verification string
	err := s.withClaim(ctx, v, kind, number, func(c *change) error {
		series := Series(kind)
		err := v.CanAccount(c.state)
		if err == ErrAlreadyAccounted && in.VoucherNumber == "" {
			// Cashflow 3 tells a voucher Fortnox lacks from one it has.
			if missing, err := recordMissing(ctx, fx, series, c.state.Verification); err != nil {
				return err
			} else if missing {
				return ErrFortnoxRecordMissing
			}
		}
		if err != nil {
			return err
		}

		verification = in.VoucherNumber
		if verification == "" {
			var err error
			if verification, err = s.book(ctx, c, kind, series, in, fx); err != nil {
				return err
			}
		}
		if err := c.q.SetVerification(ctx, db.SetVerificationParams{ID: c.claim.ID, Verification: verification}); err != nil {
			return err
		}
		return s.comment(ctx, c, "Bokförde med verifikationsnumret: "+verification)
	})
	return verification, err
}

func recordMissing(ctx context.Context, fx *fortnox.Client, series, verification string) (bool, error) {
	n, err := strconv.Atoi(verification[1:])
	if err != nil || verification[:1] != series {
		return false, nil
	}
	exists, err := fx.VoucherExists(ctx, series, n)
	if err != nil {
		return false, fortnoxProblem(err)
	}
	return !exists, nil
}

func (s *Store) book(ctx context.Context, c *change, kind Kind, series string, in AccountingInput, fx *fortnox.Client) (string, error) {
	details, err := c.q.GetVoucherDetails(ctx, c.claim.ID)
	if err != nil {
		return "", err
	}
	accounts, err := fx.Accounts(ctx)
	if err != nil {
		return "", fortnoxProblem(err)
	}
	costCentres, err := fx.CostCentres(ctx)
	if err != nil {
		return "", fortnoxProblem(err)
	}
	if err := in.validate(details.TotalOre, accounts, costCentres); err != nil {
		return "", err
	}

	description := VoucherDescription(number(c.claim), c.claim.Description)
	if n, found, err := fx.FindVoucher(ctx, series, description); err != nil {
		return "", fortnoxProblem(err)
	} else if found {
		return "", VoucherExistsProblem(series + strconv.Itoa(n))
	}
	date := ""
	if details.Date.Valid {
		date = details.Date.Time.Format(time.DateOnly)
	}
	n, err := fx.CreateVoucher(ctx, fortnox.NewVoucher{
		Series: series, Description: description, TransactionDate: date, Rows: in.Rows,
	})
	if err != nil {
		return "", fortnoxProblem(err)
	}
	return series + strconv.Itoa(n), nil
}

// FortnoxError is Fortnox refusing a voucher; Message is Fortnox's own words.
type FortnoxError struct{ Message string }

func (e *FortnoxError) Error() string { return "fortnox refused: " + e.Message }

func fortnoxProblem(err error) error {
	var api *fortnox.APIError
	switch {
	case errors.Is(err, fortnox.ErrNotConnected):
		return ErrFortnoxNotConnected
	case errors.As(err, &api) && api.Status < 500:
		return &FortnoxError{Message: api.Message}
	}
	return err
}

// ---- Drafts ----

// Draft is the voucher the accounting form starts from: one debit row per
// budget line from the accounts GOrdian lists for it, and the balancing
// credit row.
type Draft struct {
	Series          string
	Description     string
	TransactionDate string
	TotalOre        int64
	Rows            []DraftRow
}

type DraftRow struct {
	Account    int // 0 when GOrdian has no account for the budget line
	CostCentre string
	// Label says where the row comes from, e.g. the budget line.
	Label     string
	DebitOre  int64
	CreditOre int64
	// Balancing is the credit row against the debt account.
	Balancing bool
}

type DraftPart struct {
	CostCentre, SecondaryCostCentre, BudgetLine string
	AmountOre                                   int64
}

// BuildDraft ports draftsFromParts (frontend) and the recommended account
// and cost centre of PartRecommendationsMixin. Parts that end up on the
// same row are merged; parts without a known account stay apart, for the
// accountant to fill in.
func BuildDraft(kind Kind, number int64, description, date string, parts []DraftPart, tree []budget.CostCentre, costCentres []fortnox.CostCentre) Draft {
	d := Draft{Series: Series(kind), Description: VoucherDescription(number, description), TransactionDate: date}
	merged := map[[3]string]int{}
	for _, p := range parts {
		row := DraftRow{
			Account:    firstAccount(tree, p),
			CostCentre: MatchCostCentre(costCentres, p.CostCentre, p.SecondaryCostCentre),
			Label:      partLabel(p),
			DebitOre:   p.AmountOre,
		}
		d.TotalOre += p.AmountOre
		key := [3]string{strconv.Itoa(row.Account), row.CostCentre, normalise(row.Label)}
		if i, ok := merged[key]; ok && row.Account != 0 {
			d.Rows[i].DebitOre += row.DebitOre
			continue
		}
		if row.Account != 0 {
			merged[key] = len(d.Rows)
		}
		d.Rows = append(d.Rows, row)
	}
	d.Rows = append(d.Rows, DraftRow{Account: CreditAccount(kind), Label: "", CreditOre: d.TotalOre, Balancing: true})
	return d
}

// partLabel names a part's budget line in full, e.g. "Ada › Kärnverksamhet › Fika".
func partLabel(p DraftPart) string {
	var names []string
	for _, name := range []string{p.CostCentre, p.SecondaryCostCentre, p.BudgetLine} {
		if name = strings.TrimSpace(name); name != "" {
			names = append(names, name)
		}
	}
	return strings.Join(names, " › ")
}

func firstAccount(tree []budget.CostCentre, p DraftPart) int {
	if line := budget.Find(tree, p.CostCentre, p.SecondaryCostCentre, p.BudgetLine); line != nil && len(line.Accounts) > 0 {
		return line.Accounts[0]
	}
	return 0
}

// MatchCostCentre finds the Fortnox cost centre for a claim's cost centre:
// by name, or as "<cost centre> - <secondary>", which is how Fortnox names
// some. Cashflow 3 matches the latter fuzzily (rapidfuzz, cutoff 90); this
// allows the same small differences in spelling.
func MatchCostCentre(costCentres []fortnox.CostCentre, cc, secondary string) string {
	want := normalise(cc)
	for _, c := range costCentres {
		if normalise(c.Description) == want {
			return c.Code
		}
	}
	composed := normalise(cc + " - " + secondary)
	best, bestScore := "", 0.0
	for _, c := range costCentres {
		if score := similarity(normalise(c.Description), composed); score > bestScore {
			best, bestScore = c.Code, score
		}
	}
	if bestScore >= 0.9 {
		return best
	}
	return ""
}

func normalise(s string) string { return strings.ToLower(strings.Join(strings.Fields(s), " ")) }

// similarity is 1 minus the edit distance relative to the longer string.
func similarity(a, b string) float64 {
	ra, rb := []rune(a), []rune(b)
	longest := max(len(ra), len(rb))
	if longest == 0 {
		return 1
	}
	prev := make([]int, len(rb)+1)
	for j := range prev {
		prev[j] = j
	}
	for i := 1; i <= len(ra); i++ {
		cur := make([]int, len(rb)+1)
		cur[0] = i
		for j := 1; j <= len(rb); j++ {
			cost := 1
			if ra[i-1] == rb[j-1] {
				cost = 0
			}
			cur[j] = min(prev[j]+1, cur[j-1]+1, prev[j-1]+cost)
		}
		prev = cur
	}
	return 1 - float64(prev[len(rb)])/float64(longest)
}
