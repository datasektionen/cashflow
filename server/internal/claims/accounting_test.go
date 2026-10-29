package claims

import (
	"context"
	"errors"
	"net/http"
	"net/http/httptest"
	"net/url"
	"slices"
	"testing"

	"github.com/datasektionen/cashflow/server/internal/budget"
	"github.com/datasektionen/cashflow/server/internal/fortnox"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

// testFortnox is a client for a fake Fortnox, connected by "kassor".
func testFortnox(t *testing.T, f *fixtures) (*fortnox.Client, *fortnox.Fake) {
	t.Helper()
	fake := fortnox.NewFake()
	server := httptest.NewServer(fake)
	t.Cleanup(server.Close)
	fx := fortnox.New(fortnox.Config{ClientID: "id", ClientSecret: "secret", APIURL: server.URL + "/3", AuthURL: server.URL + "/oauth-v1"}, f.pool)

	// The OAuth dance: the fake approves at once and redirects with a code.
	noRedirects := &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	res, err := noRedirects.Get(fx.AuthCodeURL("https://cashflow.test/fortnox/auth/complete", "s"))
	if err != nil {
		t.Fatal(err)
	}
	location, _ := url.Parse(res.Header.Get("Location"))
	if location.Query().Get("state") != "s" {
		t.Fatalf("state not passed back: %s", location)
	}
	f.profile("kassor")
	if err := fx.Connect(context.Background(), "kassor", location.Query().Get("code"), "https://cashflow.test/fortnox/auth/complete"); err != nil {
		t.Fatal(err)
	}
	return fx, fake
}

var accountant = viewer("kassor", map[string]hive.Grant{perm.Accounting: all})

func TestAccountWithVoucherNumber(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	n := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, true}}, paid: true})

	if _, err := s.Account(ctx, accountant, Expense, n, AccountingInput{VoucherNumber: "12"}, nil); !slices.Equal(codes(err), []string{"voucher_number:voucher_number.format"}) {
		t.Errorf("bad voucher number: %v", err)
	}
	// Without Fortnox only existing voucher numbers can be recorded.
	if _, err := s.Account(ctx, accountant, Expense, n, AccountingInput{Rows: []fortnox.VoucherRow{{Account: 5460, Debit: 100}}}, nil); !errors.Is(err, ErrFortnoxDisabled) {
		t.Errorf("rows without fortnox: %v", err)
	}
	other := viewer("bertil", map[string]hive.Grant{perm.Accounting: scoped("mottagningen")})
	if _, err := s.Account(ctx, other, Expense, n, AccountingInput{VoucherNumber: "E7"}, nil); !errors.Is(err, ErrNotPermitted) && !errors.Is(err, ErrNotFound) {
		t.Errorf("other cost centre: %v", err)
	}

	got, err := s.Account(ctx, accountant, Expense, n, AccountingInput{VoucherNumber: " e7 "}, nil)
	if err != nil || got != "E7" {
		t.Fatalf("account: %q %v", got, err)
	}
	if c, _ := s.Get(ctx, accountant, Expense, n); c.Verification != "E7" || c.Stage() != StageAccounted {
		t.Errorf("verification %q stage %d", c.Verification, c.Stage())
	}
	if comments := f.comments(Expense, n); comments[len(comments)-1] != "Bokförde med verifikationsnumret: E7" {
		t.Errorf("comment %q", comments)
	}
	if mails := f.emails(); len(mails) != 1 || mails[0].To != "anna@kth.se" {
		t.Errorf("owner should be emailed: %+v", mails)
	}
	if _, err := s.Account(ctx, accountant, Expense, n, AccountingInput{VoucherNumber: "E8"}, nil); !errors.Is(err, ErrAlreadyAccounted) {
		t.Errorf("twice: %v", err)
	}
}

func TestAccountInFortnox(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	fx, fake := testFortnox(t, f)
	n := f.add(claimSpec{kind: Expense, owner: "anna", description: "Pizza", parts: []partSpec{{"Ada", 12345, true}}, paid: true})

	rows := func(debit, credit int64) AccountingInput {
		return AccountingInput{Rows: []fortnox.VoucherRow{
			{Account: 5460, CostCentre: "ADA", Debit: fortnox.Kronor(debit)},
			{Account: 2820, Credit: fortnox.Kronor(credit)},
		}}
	}
	for name, tc := range map[string]struct {
		in   AccountingInput
		want []string
	}{
		"unbalanced":   {rows(12345, 12300), []string{"rows:rows.unbalanced"}},
		"wrong total":  {rows(100, 100), []string{"rows:rows.total_mismatch"}},
		"unknown":      {AccountingInput{Rows: []fortnox.VoucherRow{{Account: 1234, CostCentre: "NOPE", Debit: 12345}, {Account: 2820, Debit: 1, Credit: 1}}}, []string{"rows[0].account:account.unknown", "rows[0].cost_centre:cost_centre.unknown", "rows[1].amount:amount.one_side"}},
		"no account":   {AccountingInput{Rows: []fortnox.VoucherRow{{Debit: 12345}, {Account: 2820, Credit: 12345}}}, []string{"rows[0].account:account.required"}},
		"empty amount": {AccountingInput{Rows: []fortnox.VoucherRow{{Account: 5460}, {Account: 2820, Credit: 12345}}}, []string{"rows[0].amount:amount.one_side"}},
	} {
		if _, err := s.Account(ctx, accountant, Expense, n, tc.in, fx); !slices.Equal(codes(err), tc.want) {
			t.Errorf("%s: got %v, want %v", name, codes(err), tc.want)
		}
	}
	if fake.VoucherCount("E") != 0 {
		t.Fatal("invalid vouchers must not reach Fortnox")
	}

	got, err := s.Account(ctx, accountant, Expense, n, rows(12345, 12345), fx)
	if err != nil || got != "E1" {
		t.Fatalf("book: %q %v", got, err)
	}
	booked := fake.Vouchers["E"][0]
	if booked.Description != VoucherDescription(n, "Pizza") || booked.TransactionDate != "2026-09-01" || booked.Rows[0].Debit != 12345 || booked.Rows[0].CostCentre != "ADA" {
		t.Errorf("booked %+v", booked)
	}
	if c, _ := s.Get(ctx, accountant, Expense, n); c.Verification != "E1" {
		t.Errorf("verification %q", c.Verification)
	}
	// Booking again: Fortnox has the voucher, so it is simply accounted.
	if _, err := s.Account(ctx, accountant, Expense, n, rows(12345, 12345), fx); !errors.Is(err, ErrAlreadyAccounted) {
		t.Errorf("twice: %v", err)
	}

	// A claim whose recorded voucher Fortnox lacks.
	lost := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, true}}, verification: "E99"})
	if _, err := s.Account(ctx, accountant, Expense, lost, rows(100, 100), fx); !errors.Is(err, ErrFortnoxRecordMissing) {
		t.Errorf("record missing: %v", err)
	}

	// A voucher booked for a claim that Cashflow never recorded is reported,
	// with its number, instead of booked twice.
	unrecorded := f.add(claimSpec{kind: Invoice, owner: "anna", description: "Hyra", parts: []partSpec{{"Ada", 500, true}}})
	fake.AddVoucher(fortnox.NewVoucher{Series: "U", Description: VoucherDescription(unrecorded, "Hyra")})
	_, err = s.Account(ctx, accountant, Invoice, unrecorded, AccountingInput{Rows: []fortnox.VoucherRow{{Account: 4010, Debit: 500}, {Account: 2440, Credit: 500}}}, fx)
	if p, ok := IsProblem(err); !ok || p.Code != "voucher_exists" || p.Detail != "U1" {
		t.Errorf("unrecorded voucher: %v", err)
	}
	if fake.VoucherCount("U") != 1 {
		t.Error("must not book twice")
	}

	// Fortnox's own refusals come back with its message.
	fake.Series = nil
	other := f.add(claimSpec{kind: Expense, owner: "anna", description: "Taxi", parts: []partSpec{{"Ada", 100, true}}})
	var refused *FortnoxError
	if _, err := s.Account(ctx, accountant, Expense, other, rows(100, 100), fx); !errors.As(err, &refused) || refused.Message == "" {
		t.Errorf("refused: %v", err)
	}
}

func TestFortnoxTokens(t *testing.T) {
	_, f := testStore(t)
	ctx := context.Background()
	fx, fake := testFortnox(t, f)

	conn, err := fx.Connection(ctx)
	if err != nil || conn == nil || conn.Username != "kassor" || conn.Name != "kassor Testsson" {
		t.Fatalf("connection %+v %v", conn, err)
	}

	// An expired access token is refreshed, and the rotated refresh token kept.
	f.pool.Exec(ctx, `UPDATE fortnox_serviceaccount SET expires_at = now() - interval '1 minute'`)
	if _, err := fx.Accounts(ctx); err != nil {
		t.Fatal(err)
	}
	if fake.Refreshes != 1 {
		t.Errorf("refreshes %d", fake.Refreshes)
	}
	var refresh string
	f.pool.QueryRow(ctx, `SELECT refresh_token FROM fortnox_serviceaccount`).Scan(&refresh)

	// A revoked access token is refreshed and the call retried.
	f.pool.Exec(ctx, `UPDATE fortnox_serviceaccount SET access_token = 'revoked'`)
	if _, err := fx.VoucherSeries(ctx); err != nil || fake.Refreshes != 2 {
		t.Errorf("revoked access token: %v, %d refreshes", err, fake.Refreshes)
	}

	// A spent refresh token means Fortnox is disconnected.
	f.pool.Exec(ctx, `UPDATE fortnox_serviceaccount SET access_token = 'revoked', refresh_token = 'spent'`)
	if _, err := fx.VoucherSeries(ctx); !errors.Is(err, fortnox.ErrNotConnected) {
		t.Errorf("spent refresh token: %v", err)
	}
	if conn, _ := fx.Connection(ctx); conn != nil {
		t.Error("a refused refresh should disconnect")
	}
	if refresh == "spent" || refresh == "" {
		t.Error("refresh token should have rotated")
	}
}

func TestBuildDraft(t *testing.T) {
	tree := []budget.CostCentre{{Name: "Ada", Secondary: []budget.SecondaryCostCentre{{Name: "Kärnverksamhet", Lines: []budget.Line{
		{Name: "Fika", Accounts: []int{5460, 5461}}, {Name: "Spel", Accounts: []int{5410}},
	}}}}}
	ccs := []fortnox.CostCentre{{Code: "ADA", Description: "Ada"}, {Code: "MOTTPH", Description: "Mottagningen - Phadderiet"}}
	d := BuildDraft(Expense, 7, "Fika", "2026-09-01", []DraftPart{
		{"Ada", "Kärnverksamhet", "Fika", 100},
		{"ada", "kärnverksamhet ", "fika", 50}, // same line, merged
		{"Ada", "Kärnverksamhet", "Spel", 25},
		{"Mottagningen", "Phaderiet", "Tröjor", 10}, // no budget line; fuzzy cost centre
		{"Okänd", "", "", 5},
	}, tree, ccs)

	if d.Series != "E" || d.Description != "(7) Fika" || d.TotalOre != 190 {
		t.Errorf("draft %+v", d)
	}
	want := []DraftRow{
		{Account: 5460, CostCentre: "ADA", Label: "Ada › Kärnverksamhet › Fika", DebitOre: 150},
		{Account: 5410, CostCentre: "ADA", Label: "Ada › Kärnverksamhet › Spel", DebitOre: 25},
		{Account: 0, CostCentre: "MOTTPH", Label: "Mottagningen › Phaderiet › Tröjor", DebitOre: 10},
		{Account: 0, CostCentre: "", Label: "Okänd", DebitOre: 5},
		{Account: 2820, CreditOre: 190, Balancing: true},
	}
	if !slices.Equal(d.Rows, want) {
		t.Errorf("rows\n got %+v\nwant %+v", d.Rows, want)
	}
	if got := BuildDraft(Invoice, 1, "x", "", nil, nil, nil); got.Series != "U" || got.Rows[0].Account != 2440 {
		t.Errorf("invoice draft %+v", got)
	}
}
