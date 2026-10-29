package claims

import (
	"context"
	"fmt"
	"math/rand/v2"
	"net/url"
	"os"
	"slices"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/datasektionen/cashflow/server/internal/database"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

// These tests run against a real Postgres with Cashflow 3's schema, because
// the rules live in SQL. Set TEST_DATABASE_URL to a server where the user may
// create databases (`make services` provides one); each run uses a fresh
// database and drops it afterwards.
func testStore(t *testing.T) (*Store, *fixtures) {
	t.Helper()
	base := os.Getenv("TEST_DATABASE_URL")
	if base == "" {
		t.Skip("TEST_DATABASE_URL not set")
	}
	ctx := context.Background()

	admin, err := pgx.Connect(ctx, base)
	if err != nil {
		t.Fatal(err)
	}
	name := fmt.Sprintf("cashflow_test_%d", rand.Uint32())
	if _, err := admin.Exec(ctx, "CREATE DATABASE "+name); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		admin.Exec(context.Background(), "DROP DATABASE "+name+" WITH (FORCE)")
		admin.Close(context.Background())
	})

	u, _ := url.Parse(base)
	u.Path = "/" + name
	schema, err := os.ReadFile("../database/cashflow3/schema.sql")
	if err != nil {
		t.Fatal(err)
	}
	conn, err := pgx.Connect(ctx, u.String())
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close(ctx)
	if _, err := conn.Exec(ctx, string(schema)); err != nil {
		t.Fatalf("load schema: %v", err)
	}
	if err := database.Migrate(u.String()); err != nil {
		t.Fatalf("migrate: %v", err)
	}

	pool, err := pgxpool.New(ctx, u.String())
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(pool.Close)
	return NewStore(pool, "https://cashflow.test"), &fixtures{t: t, pool: pool, profiles: map[string]int64{}}
}

type fixtures struct {
	t        *testing.T
	pool     *pgxpool.Pool
	profiles map[string]int64
}

func (f *fixtures) exec(sql string, args ...any) int64 {
	f.t.Helper()
	var id int64
	if err := f.pool.QueryRow(context.Background(), sql+" RETURNING id", args...).Scan(&id); err != nil {
		f.t.Fatalf("%s: %v", sql, err)
	}
	return id
}

func (f *fixtures) profile(username string) int64 {
	if id, ok := f.profiles[username]; ok {
		return id
	}
	userID := f.exec(`INSERT INTO auth_user (username, first_name, last_name, email, password, is_superuser, is_staff, is_active, date_joined)
		VALUES ($1::text, $1::text, 'Testsson', $1::text || '@kth.se', '!', false, false, true, now())`, username)
	id := f.exec(`INSERT INTO core_profile (user_id, bank_account, sorting_number, bank_name) VALUES ($1, '', '', '')`, userID)
	f.profiles[username] = id
	return id
}

type claimSpec struct {
	kind         Kind
	owner        string
	description  string
	parts        []partSpec
	confirmed    bool
	paid         bool
	flagged      bool
	verification string
	date         time.Time
}

type partSpec struct {
	costCentre string
	amountOre  int64
	attested   bool
}

// add inserts a claim and returns its public number.
func (f *fixtures) add(c claimSpec) int64 {
	f.t.Helper()
	owner := f.profile(c.owner)
	treasurer := f.profile("kassor")
	if c.date.IsZero() {
		c.date = time.Date(2026, 9, 1, 0, 0, 0, 0, time.UTC)
	}
	if c.description == "" {
		c.description = "Claim"
	}
	var number int64
	var expenseID, invoiceID any
	switch c.kind {
	case Expense:
		var confirmedBy, payment any
		if c.confirmed {
			f.pool.QueryRow(context.Background(), "SELECT user_id FROM core_profile WHERE id = $1", treasurer).Scan(&confirmedBy)
		}
		if c.paid {
			payment = f.exec(`INSERT INTO expenses_payment (date, payer_id, receiver_id) VALUES (now(), $1, $2)`, treasurer, owner)
		}
		number = f.exec(`INSERT INTO expenses_expensedata (expense_date, confirmed_at, is_flagged, confirmed_by_id, reimbursement_id)
			VALUES ($1, CASE WHEN $2::int IS NULL THEN NULL ELSE now() END, $3, $2, $4)`, c.date, confirmedBy, c.flagged, payment)
		expenseID = number
	case Invoice:
		var paidBy any
		if c.paid {
			paidBy = treasurer
		}
		number = f.exec(`INSERT INTO invoices_invoicedata (invoice_date, invoice_number, due_date, paid_at, paid_by_id)
			VALUES ($1, 'F1', $1, CASE WHEN $2::bigint IS NULL THEN NULL ELSE now() END, $2)`, c.date, paidBy)
		invoiceID = number
	}
	claimID := f.exec(`INSERT INTO core_claim (description, created_date, verification, expense_data_id, invoice_data_id, owner_id)
		VALUES ($1, $2, $3, $4, $5, $6)`, c.description, c.date, c.verification, expenseID, invoiceID, owner)
	for _, p := range c.parts {
		var attester any
		if p.attested {
			attester = treasurer
		}
		f.exec(`INSERT INTO core_claimpart (claim_id, cost_centre, secondary_cost_centre, budget_line, amount, attested_by_id, attest_date)
			VALUES ($1, $2, '', '', $3::numeric / 100, $4, CASE WHEN $4::bigint IS NULL THEN NULL ELSE now() END)`,
			claimID, p.costCentre, p.amountOre, attester)
	}
	return number
}

func viewer(username string, grants map[string]hive.Grant) Viewer {
	return Viewer{Username: username, Perms: perm.New(username, hive.Permissions(grants))}
}

var all = hive.Grant{All: true}

func scoped(scopes ...string) hive.Grant { return hive.Grant{Scopes: scopes} }

// numbers lists the claim numbers v gets for f, as "e<n>" or "i<n>".
func numbers(t *testing.T, s *Store, v Viewer, f Filter) []string {
	t.Helper()
	f.PageSize = MaxPageSize
	list, total, err := s.List(context.Background(), v, f)
	if err != nil {
		t.Fatal(err)
	}
	if total != len(list) {
		t.Errorf("total %d but %d rows", total, len(list))
	}
	var out []string
	for _, c := range list {
		out = append(out, fmt.Sprintf("%c%d", c.Kind[0], c.Number))
	}
	slices.Sort(out)
	return out
}

func expectNumbers(t *testing.T, got []string, want ...string) {
	t.Helper()
	slices.Sort(want)
	if !slices.Equal(got, want) {
		t.Errorf("got %v, want %v", got, want)
	}
}

func TestVisibility(t *testing.T) {
	s, f := testStore(t)
	ada := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, false}}})
	dsys := f.add(claimSpec{kind: Expense, owner: "bertil", parts: []partSpec{{"DSys", 100, false}}})
	mixed := f.add(claimSpec{kind: Invoice, owner: "bertil", parts: []partSpec{{"Other", 100, false}, {"ADA", 50, false}}})

	expectNumbers(t, numbers(t, s, viewer("anna", nil), Filter{}), fmt.Sprintf("e%d", ada))
	expectNumbers(t, numbers(t, s, viewer("nobody", nil), Filter{}))

	// Scopes match cost centres case-insensitively, through any part.
	adaAttester := viewer("cecilia", map[string]hive.Grant{perm.Attest: scoped("ada")})
	expectNumbers(t, numbers(t, s, adaAttester, Filter{}), fmt.Sprintf("e%d", ada), fmt.Sprintf("i%d", mixed))

	// Accounting and view-expenses scopes also widen visibility.
	expectNumbers(t, numbers(t, s, viewer("david", map[string]hive.Grant{perm.Accounting: scoped("dsys")}), Filter{}), fmt.Sprintf("e%d", dsys))
	expectNumbers(t, numbers(t, s, viewer("erik", map[string]hive.Grant{perm.ViewExpenses: scoped("dsys")}), Filter{}), fmt.Sprintf("e%d", dsys))

	// Paying, confirming or viewing everything shows everything.
	for _, p := range []string{perm.Pay, perm.Confirm, perm.ViewAll} {
		got := numbers(t, s, viewer("fia", map[string]hive.Grant{p: all}), Filter{})
		if len(got) != 3 {
			t.Errorf("%s: got %v, want all 3", p, got)
		}
	}

	// Single lookups follow the same rule, and Mine narrows to one's own.
	if _, err := s.Get(context.Background(), viewer("anna", nil), Expense, dsys); err != ErrNotFound {
		t.Errorf("anna must not see bertil's claim, got %v", err)
	}
	expectNumbers(t, numbers(t, s, viewer("bertil", map[string]hive.Grant{perm.ViewAll: all}), Filter{Mine: true}),
		fmt.Sprintf("e%d", dsys), fmt.Sprintf("i%d", mixed))
}

func TestAttestQueue(t *testing.T) {
	s, f := testStore(t)
	e := func(n int64) string { return fmt.Sprintf("e%d", n) }
	others := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, false}}})
	ownExpense := f.add(claimSpec{kind: Expense, owner: "cecilia", parts: []partSpec{{"Ada", 100, false}}})
	ownInvoice := f.add(claimSpec{kind: Invoice, owner: "cecilia", parts: []partSpec{{"Ada", 100, false}}})
	f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, true}}}) // fully attested
	adaDone := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, true}, {"DSys", 100, false}}})
	dsysOnly := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"DSys", 100, false}}})
	adaAttester := viewer("cecilia", map[string]hive.Grant{perm.Attest: scoped("ada")})

	// Only parts still to attest in one's cost centres; one's own invoices but not expenses.
	expectNumbers(t, numbers(t, s, adaAttester, Filter{Queue: QueueAttest}), e(others), fmt.Sprintf("i%d", ownInvoice))

	// View-all admins see every unattested part, from any cost centre...
	got := numbers(t, s, viewer("zelda", map[string]hive.Grant{perm.ViewAll: all}), Filter{Queue: QueueAttest})
	expectNumbers(t, got, e(others), e(ownExpense), fmt.Sprintf("i%d", ownInvoice), e(adaDone), e(dsysOnly))
	// ...but never their own expenses.
	got = numbers(t, s, viewer("anna", map[string]hive.Grant{perm.ViewAll: all}), Filter{Queue: QueueAttest})
	expectNumbers(t, got, e(ownExpense), fmt.Sprintf("i%d", ownInvoice))

	if _, _, err := s.List(context.Background(), viewer("anna", nil), Filter{Queue: QueueAttest}); err != ErrForbiddenQueue {
		t.Errorf("want ErrForbiddenQueue for someone who cannot attest, got %v", err)
	}
}

func TestConfirmPayAndAccountQueues(t *testing.T) {
	s, f := testStore(t)
	unconfirmed := f.add(claimSpec{kind: Expense, owner: "anna", parts: []partSpec{{"Ada", 100, true}}})
	payable := f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, parts: []partSpec{{"Ada", 100, true}}})
	f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, parts: []partSpec{{"Ada", 100, false}}}) // confirmed, not attested
	payableInvoice := f.add(claimSpec{kind: Invoice, owner: "anna", parts: []partSpec{{"Ada", 100, true}}})
	paid := f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, paid: true, parts: []partSpec{{"Ada", 100, true}}})
	paidInvoice := f.add(claimSpec{kind: Invoice, owner: "anna", paid: true, parts: []partSpec{{"DSys", 100, true}}})
	f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, paid: true, verification: "E1", parts: []partSpec{{"Ada", 100, true}}})

	confirmer := viewer("kassor", map[string]hive.Grant{perm.Confirm: all})
	expectNumbers(t, numbers(t, s, confirmer, Filter{Queue: QueueConfirm}), fmt.Sprintf("e%d", unconfirmed))

	payer := viewer("kassor", map[string]hive.Grant{perm.Pay: all})
	expectNumbers(t, numbers(t, s, payer, Filter{Queue: QueuePay}), fmt.Sprintf("e%d", payable), fmt.Sprintf("i%d", payableInvoice))

	accountant := viewer("bok", map[string]hive.Grant{perm.Accounting: scoped("ada")})
	expectNumbers(t, numbers(t, s, accountant, Filter{Queue: QueueAccount}), fmt.Sprintf("e%d", paid))
	allAccountant := viewer("bok", map[string]hive.Grant{perm.Accounting: all})
	expectNumbers(t, numbers(t, s, allAccountant, Filter{Queue: QueueAccount}), fmt.Sprintf("e%d", paid), fmt.Sprintf("i%d", paidInvoice))

	if n, err := s.Count(context.Background(), payer, QueuePay); err != nil || n != 2 {
		t.Errorf("Count(pay) = %d, %v; want 2", n, err)
	}
}

func TestSearchSortAndPaging(t *testing.T) {
	s, f := testStore(t)
	viewAll := viewer("admin", map[string]hive.Grant{perm.ViewAll: all})
	day := func(d int) time.Time { return time.Date(2026, 9, d, 0, 0, 0, 0, time.UTC) }
	pizza := f.add(claimSpec{kind: Expense, owner: "anna", description: "Pizza till mötet", date: day(3), parts: []partSpec{{"Ada", 30000, false}}})
	f.add(claimSpec{kind: Expense, owner: "bertil", description: "Kaffe 100% arabica", date: day(1), parts: []partSpec{{"Ada", 5000, false}}})
	f.add(claimSpec{kind: Expense, owner: "bertil", description: "Kaffe 100 gram", date: day(2), parts: []partSpec{{"Ada", 7000, false}}})

	expectNumbers(t, numbers(t, s, viewAll, Filter{Query: "pizza"}), fmt.Sprintf("e%d", pizza))
	expectNumbers(t, numbers(t, s, viewAll, Filter{Query: fmt.Sprintf("#%d", pizza)}), fmt.Sprintf("e%d", pizza))
	expectNumbers(t, numbers(t, s, viewAll, Filter{Query: "anna"}), fmt.Sprintf("e%d", pizza))
	// % is literal, not a wildcard.
	expectNumbers(t, numbers(t, s, viewAll, Filter{Query: "100%"}), "e2")

	list, total, err := s.List(context.Background(), viewAll, Filter{Sort: SortAmount, Descending: true, PageSize: 2, Page: 1})
	if err != nil || total != 3 || len(list) != 2 || list[0].AmountOre != 30000 || list[1].AmountOre != 7000 {
		t.Errorf("page 1 by amount: total %d, %+v, %v", total, list, err)
	}
	list, _, _ = s.List(context.Background(), viewAll, Filter{Sort: SortAmount, Descending: true, PageSize: 2, Page: 2})
	if len(list) != 1 || list[0].AmountOre != 5000 {
		t.Errorf("page 2 by amount: %+v", list)
	}
	// Lists default to newest first.
	list, _, _ = s.List(context.Background(), viewAll, Filter{})
	if list[0].Number != pizza {
		t.Errorf("default order should start with the newest, got #%d", list[0].Number)
	}
}

func TestSummaryFields(t *testing.T) {
	s, f := testStore(t)
	n := f.add(claimSpec{kind: Expense, owner: "anna", flagged: true, confirmed: true,
		parts: []partSpec{{"Ada", 12345, true}, {"DSys", 55, true}, {"Ada", 100, true}}})
	c, err := s.Get(context.Background(), viewer("anna", nil), Expense, n)
	if err != nil {
		t.Fatal(err)
	}
	if c.AmountOre != 12500 || !slices.Equal(c.CostCentres, []string{"Ada", "DSys"}) || !c.Attested || !c.Confirmed || !c.Flagged {
		t.Errorf("unexpected summary %+v", c)
	}
	if c.Stage() != StageConfirmed {
		t.Errorf("stage %d, want confirmed", c.Stage())
	}
}
