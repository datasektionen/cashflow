// Command seed fills a development database with realistic claims: every
// workflow stage, the nyckeln test users from compose.next.yaml, several cost
// centres, comments, payments and receipt files in S3.
//
//	cd server && go run ./cmd/seed          # refuses if claims exist
//	cd server && go run ./cmd/seed -reset   # replaces all claims
//
// It only runs against a database on localhost.
package main

import (
	"bytes"
	"context"
	"flag"
	"fmt"
	"log"
	"log/slog"
	"math/rand/v2"
	"net/url"
	"os"
	"time"

	"github.com/jackc/pgx/v5"

	"github.com/datasektionen/cashflow/server/internal/budget"
	"github.com/datasektionen/cashflow/server/internal/config"
	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/storage"
)

func main() {
	reset := flag.Bool("reset", false, "delete all claims, comments, files and payments first")
	flag.Parse()
	if err := run(context.Background(), *reset); err != nil {
		log.Fatal(err)
	}
}

type user struct {
	username, first, last, email string
	profileID                    int64
}

var users = []*user{
	{username: "turetek", first: "Ture", last: "Teknolog", email: "turetek@kth.se"},
	{username: "diadat", first: "Diana", last: "Datalog", email: "diadat@kth.se"},
	{username: "marmed", first: "Martin", last: "Median", email: "marmed@kth.se"},
	{username: "jobjav", first: "Jobbig", last: `"Speciell" Jävel`, email: "jobjav@kth.se"},
	{username: "sauron", first: "Sauron", last: "Mordor", email: "sauron@kth.se"},
	{username: "bilbek", first: "Bilbo", last: "Baggins", email: "bilbek@kth.se"},
}

// Cost centres and their budget lines; the first two match nyckeln's scoped
// grants for diadat and bilbek. All five are in GOrdian, whose real budget
// lines replace these when it answers (useRealBudget), so the budget page,
// usage warnings and voucher drafts show real numbers in development.
var seedBudget = map[string][][2]string{
	"Sektionslokalsgruppen": {{"Inköp", "Förbrukningsmaterial"}, {"Inköp", "Städmaterial"}, {"Evenemang", "Pubkvällar"}},
	"Mottagningen 2026":     {{"Mottagningsveckan", "Mat"}, {"Mottagningsveckan", "Aktiviteter"}, {"Phadderiet", "Tröjor"}},
	"Ada":                   {{"Kärnverksamhet", "Fika"}, {"Kärnverksamhet", "Spel"}},
	"Näringslivsgruppen":    {{"Arbetsmarknadsdag", "Lokalhyra"}, {"Arbetsmarknadsdag", "Tryck"}},
	"Studienämnden":         {{"Studiesociala", "Tentapub"}, {"Studiesociala", "Läxhjälp"}},
}

var costCentres = []string{"Sektionslokalsgruppen", "Mottagningen 2026", "Ada", "Näringslivsgruppen", "Studienämnden"}

var expenseDescriptions = []string{
	"Kaffe och mjölk till Meta", "Pizza till styrelsemöte", "Diskmedel och svampar", "Glödlampor till Meta",
	"Fika till läxhjälpen", "Brädspel till sektionslokalen", "Mat till mottagningens sittning", "Tröjtryck phadderiet",
	"Godis till tentapuben", "Pappersmuggar och servetter", "Hyra av släpvagn", "Skrivarpapper och toner",
	"Frukost till arbetsmarknadsdagen", "Batterier till trådlösa mikrofoner", "Saft och kakor till öppet hus",
}

var invoiceSuppliers = []string{"Systembolaget AB", "Clas Ohlson AB", "Tryckeriet i Stockholm", "Lokalbokningen KTH", "Elgiganten AB", "Pizzeria Dalia"}

type stage int

const (
	submitted stage = iota
	attested
	confirmed
	paid
	accounted
)

func run(ctx context.Context, reset bool) error {
	if err := config.LoadDotEnv(".env"); err != nil {
		return err
	}
	env, err := config.FromEnv()
	if err != nil {
		return err
	}
	if u, err := url.Parse(env.DatabaseURL); err != nil || (u.Hostname() != "localhost" && u.Hostname() != "127.0.0.1") {
		return fmt.Errorf("refusing to seed a database that is not on localhost")
	}

	conn, err := pgx.Connect(ctx, env.DatabaseURL)
	if err != nil {
		return err
	}
	defer conn.Close(ctx)
	files, err := storage.New(ctx, env.S3)
	if err != nil {
		return err
	}

	var existing int
	if err := conn.QueryRow(ctx, "SELECT count(*) FROM core_claim").Scan(&existing); err != nil {
		return err
	}
	if existing > 0 && !reset {
		return fmt.Errorf("the database already has %d claims; run with -reset to replace them", existing)
	}

	tx, err := conn.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx)

	if reset {
		if _, err := tx.Exec(ctx, `TRUNCATE core_comment, core_file, core_claimpart, core_claim,
			expenses_expensedata, invoices_invoicedata, expenses_payment RESTART IDENTITY CASCADE`); err != nil {
			return err
		}
	}

	q := db.New(tx)
	for _, u := range users {
		if _, err := q.UpsertUser(ctx, db.UpsertUserParams{Username: u.username, FirstName: u.first, LastName: u.last, Email: u.email}); err != nil {
			return err
		}
		if err := tx.QueryRow(ctx, `SELECT p.id FROM core_profile p JOIN auth_user u ON u.id = p.user_id WHERE u.username = $1`, u.username).Scan(&u.profileID); err != nil {
			return err
		}
	}
	// Bank details for everyone but jobjav, who shows the "missing" state.
	if _, err := tx.Exec(ctx, `UPDATE core_profile p SET sorting_number = '8327', bank_account = '9' || lpad(p.id::text, 9, '0'), bank_name = 'Swedbank'
		FROM auth_user u WHERE u.id = p.user_id AND u.username <> 'jobjav'`); err != nil {
		return err
	}

	useRealBudget(ctx, env.BudgetURL)
	s := &seeder{tx: tx, files: files, rnd: rand.New(rand.NewPCG(2026, 10)), now: time.Now()}
	if err := s.claims(ctx); err != nil {
		return err
	}
	if err := tx.Commit(ctx); err != nil {
		return err
	}
	fmt.Printf("Seeded %d expenses and %d invoices for %d users.\n", s.expenses, s.invoices, len(users))
	return nil
}

type seeder struct {
	tx                 pgx.Tx
	files              *storage.Store
	rnd                *rand.Rand
	now                time.Time
	expenses, invoices int
}

func (s *seeder) pick(n int) int { return s.rnd.IntN(n) }

func (s *seeder) daysAgo(min, max int) time.Time {
	return s.now.AddDate(0, 0, -(min + s.pick(max-min+1)))
}

func (s *seeder) claims(ctx context.Context) error {
	treasurer := users[0]
	// Expenses: a spread of stages, oldest furthest along.
	plan := []stage{
		submitted, submitted, submitted, submitted, submitted, submitted, submitted,
		attested, attested, attested, attested,
		confirmed, confirmed, confirmed,
		paid, paid, paid,
		accounted, accounted, accounted, accounted,
	}
	for i, st := range plan {
		// Rotate owners against the cost centre rotation (i%5), so every
		// attester has claims from others in their cost centres.
		owner := users[1+(i+i/5)%(len(users)-1)]
		if i%7 == 3 {
			owner = treasurer // the treasurer's own expenses must stay out of their attest queue
		}
		// Flag claims in another cost centre than the attesters' own (i%5 == 0).
		flagged := st == submitted && i%5 == 2
		if err := s.expense(ctx, owner, st, flagged, i); err != nil {
			return err
		}
	}
	for i, st := range []stage{submitted, submitted, submitted, attested, attested, paid, paid, accounted} {
		if err := s.invoice(ctx, users[(i*2)%len(users)], st, i); err != nil {
			return err
		}
	}
	return nil
}

// partsFor splits amountOre over one or two cost centres.
func (s *seeder) partsFor(i int, amountOre int64) []part {
	cc := costCentres[i%len(costCentres)]
	lines := seedBudget[cc]
	line := lines[s.pick(len(lines))]
	if i%4 != 0 {
		return []part{{cc, line[0], line[1], amountOre}}
	}
	cc2 := costCentres[(i+2)%len(costCentres)]
	line2 := seedBudget[cc2][0]
	first := amountOre * int64(40+s.pick(30)) / 100
	return []part{{cc, line[0], line[1], first}, {cc2, line2[0], line2[1], amountOre - first}}
}

type part struct {
	costCentre, secondary, budgetLine string
	amountOre                         int64
}

func (s *seeder) expense(ctx context.Context, owner *user, st stage, flagged bool, i int) error {
	age := 3 + int(st)*12 + s.pick(10)
	date := s.now.AddDate(0, 0, -age)
	amount := int64(4900 + s.pick(250000))
	description := expenseDescriptions[i%len(expenseDescriptions)]

	var confirmedBy *int64
	var confirmedAt *time.Time
	if st >= confirmed {
		id, at := s.userID(ctx, users[0]), date.AddDate(0, 0, 4)
		confirmedBy, confirmedAt = &id, &at
	}
	var paymentID *int64
	if st >= paid {
		var id int64
		if err := s.tx.QueryRow(ctx, `INSERT INTO expenses_payment (date, payer_id, receiver_id) VALUES ($1, $2, $3) RETURNING id`,
			date.AddDate(0, 0, 7), users[0].profileID, owner.profileID).Scan(&id); err != nil {
			return err
		}
		paymentID = &id
	}

	var dataID int64
	if err := s.tx.QueryRow(ctx, `INSERT INTO expenses_expensedata (expense_date, confirmed_at, is_flagged, confirmed_by_id, reimbursement_id)
		VALUES ($1, $2, $3, $4, $5) RETURNING id`, date, confirmedAt, flagged, confirmedBy, paymentID).Scan(&dataID); err != nil {
		return err
	}
	verification := ""
	if st == accounted {
		verification = fmt.Sprintf("E%d", 100+dataID)
	}
	claimID, err := s.claim(ctx, owner, description, date, verification, &dataID, nil)
	if err != nil {
		return err
	}
	if err := s.parts(ctx, claimID, s.partsFor(i, amount), st >= attested, date); err != nil {
		return err
	}
	if err := s.attach(ctx, claimID, dataID, owner, description, amount, date, i%3 == 0); err != nil {
		return err
	}
	if err := s.comments(ctx, claimID, owner, st, flagged, paymentID, date); err != nil {
		return err
	}
	s.expenses++
	return nil
}

func (s *seeder) invoice(ctx context.Context, owner *user, st stage, i int) error {
	date := s.daysAgo(5+int(st)*10, 12+int(st)*10)
	due := date.AddDate(0, 0, 30)
	amount := int64(50000 + s.pick(1500000))
	supplier := invoiceSuppliers[i%len(invoiceSuppliers)]

	var paidAt *time.Time
	var paidBy *int64
	if st >= paid {
		at := date.AddDate(0, 0, 10)
		paidAt, paidBy = &at, &users[0].profileID
	}
	var dataID int64
	if err := s.tx.QueryRow(ctx, `INSERT INTO invoices_invoicedata (invoice_date, invoice_number, due_date, paid_at, paid_by_id)
		VALUES ($1, $2, $3, $4, $5) RETURNING id`, date, fmt.Sprintf("F%d", 20260000+s.pick(9999)), due, paidAt, paidBy).Scan(&dataID); err != nil {
		return err
	}
	verification := ""
	if st == accounted {
		verification = fmt.Sprintf("U%d", 40+dataID)
	}
	claimID, err := s.claim(ctx, owner, "Faktura från "+supplier, date, verification, nil, &dataID)
	if err != nil {
		return err
	}
	if err := s.parts(ctx, claimID, s.partsFor(i+1, amount), st >= attested, date); err != nil {
		return err
	}
	if err := s.attach(ctx, claimID, dataID, owner, "Faktura från "+supplier, amount, date, true); err != nil {
		return err
	}
	if err := s.comments(ctx, claimID, owner, st, false, nil, date); err != nil {
		return err
	}
	s.invoices++
	return nil
}

func (s *seeder) claim(ctx context.Context, owner *user, description string, date time.Time, verification string, expenseID, invoiceID *int64) (int64, error) {
	var id int64
	err := s.tx.QueryRow(ctx, `INSERT INTO core_claim (description, created_date, verification, expense_data_id, invoice_data_id, owner_id)
		VALUES ($1, $2, $3, $4, $5, $6) RETURNING id`, description, date.AddDate(0, 0, 1), verification, expenseID, invoiceID, owner.profileID).Scan(&id)
	return id, err
}

func (s *seeder) parts(ctx context.Context, claimID int64, parts []part, attested bool, date time.Time) error {
	for _, p := range parts {
		var attester *int64
		var attestedAt *time.Time
		if attested {
			at := date.AddDate(0, 0, 2)
			attester, attestedAt = &users[1].profileID, &at
		}
		if _, err := s.tx.Exec(ctx, `INSERT INTO core_claimpart (claim_id, cost_centre, secondary_cost_centre, budget_line, amount, attested_by_id, attest_date)
			VALUES ($1, $2, $3, $4, $5::numeric / 100, $6, $7)`, claimID, p.costCentre, p.secondary, p.budgetLine, p.amountOre, attester, attestedAt); err != nil {
			return err
		}
	}
	return nil
}

func (s *seeder) attach(ctx context.Context, claimID, number int64, owner *user, title string, amountOre int64, date time.Time, pdf bool) error {
	var name string
	var body []byte
	if pdf {
		name, body = fmt.Sprintf("seed/%d-%d.pdf", claimID, number), receiptPDF(title, owner.first+" "+owner.last, amountOre, date)
	} else {
		img, err := receiptPNG(title, amountOre, date)
		if err != nil {
			return err
		}
		name, body = fmt.Sprintf("seed/%d-%d.png", claimID, number), img
	}
	if err := s.files.Put(ctx, name, bytes.NewReader(body)); err != nil {
		return fmt.Errorf("upload %s (is the s3 service from compose.next.yaml running?): %w", name, err)
	}
	_, err := s.tx.Exec(ctx, `INSERT INTO core_file (claim_id, file) VALUES ($1, $2)`, claimID, name)
	return err
}

// comments writes the history Cashflow 3 would have, plus a human note now and then.
func (s *seeder) comments(ctx context.Context, claimID int64, owner *user, st stage, flagged bool, paymentID *int64, from time.Time) error {
	type c struct {
		author *user
		body   string
	}
	var list []c
	if s.pick(3) == 0 {
		list = append(list, c{owner, "Kvittot är lite suddigt, men summan syns längst ner."})
	}
	if flagged {
		list = append(list, c{users[0], "Flaggar: kvittot saknar organisationsnummer. Kan du ladda upp ett nytt?"})
	}
	if st >= attested {
		list = append(list, c{users[1], "Attesterar kvittodelen"})
	}
	if st >= confirmed {
		list = append(list, c{users[0], "Jag har bekräftat kvittots giltighet."})
	}
	if paymentID != nil {
		list = append(list, c{users[0], fmt.Sprintf("Betalade ut i betalning %d", *paymentID)})
	}
	if st == accounted {
		list = append(list, c{users[5], "Bokförde i Fortnox."})
	}
	at := from.AddDate(0, 0, 1)
	for _, cm := range list {
		at = at.Add(time.Duration(6+s.pick(30)) * time.Hour)
		if at.After(s.now) {
			at = s.now.Add(-time.Hour)
		}
		if _, err := s.tx.Exec(ctx, `INSERT INTO core_comment (claim_id, date, author_id, content) VALUES ($1, $2, $3, $4)`,
			claimID, at, cm.author.profileID, cm.body); err != nil {
			return err
		}
	}
	return nil
}

func (s *seeder) userID(ctx context.Context, u *user) int64 {
	var id int64
	if err := s.tx.QueryRow(ctx, `SELECT id FROM auth_user WHERE username = $1`, u.username).Scan(&id); err != nil {
		fmt.Fprintln(os.Stderr, err)
	}
	return id
}

// useRealBudget swaps the made-up budget lines for GOrdian's, keeping only
// lines with an expense budget, so claims count against real budgets.
func useRealBudget(ctx context.Context, url string) {
	tree, err := budget.NewClient(url).Tree(ctx)
	if err != nil {
		slog.Warn("GOrdian unreachable; seeding made-up budget lines", "error", err)
		return
	}
	for _, cc := range tree {
		if _, seeded := seedBudget[cc.Name]; !seeded {
			continue
		}
		var lines [][2]string
		for _, scc := range cc.Secondary {
			for _, l := range scc.Lines {
				if l.ExpenseOre > 0 {
					lines = append(lines, [2]string{scc.Name, l.Name})
				}
			}
		}
		if len(lines) > 0 {
			seedBudget[cc.Name] = lines
		}
	}
}
