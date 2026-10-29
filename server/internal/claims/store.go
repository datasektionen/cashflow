package claims

import (
	"context"
	"errors"
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/datasektionen/cashflow/server/internal/database/db"
)

// Store reads claims. Lists are built here rather than in sqlc because their
// filters and sort vary per request, and the permission predicates below must
// be shared by listing, counting and single-claim lookups.
type Store struct {
	pool    *pgxpool.Pool
	Queries *db.Queries
	// publicURL is where emails link to, e.g. https://cashflow.datasektionen.se.
	publicURL string
}

func NewStore(pool *pgxpool.Pool, publicURL string) *Store {
	return &Store{pool: pool, Queries: db.New(pool), publicURL: publicURL}
}

// claimRows flattens Cashflow 3's claim tables into one row per claim. Part
// data is aggregated so permission checks can look at cost centres:
// lower_ccs holds every part's cost centre and unattested_ccs those of parts
// still to attest, lowercased like Hive scopes.
const claimRows = `
SELECT
	c.id,
	c.type AS kind,
	COALESCE(c.expense_data_id, c.invoice_data_id) AS number,
	c.description,
	u.username AS owner_username,
	trim(u.first_name || ' ' || u.last_name) AS owner_name,
	parts.total_ore,
	COALESCE(e.expense_date, i.invoice_date, i.paid_at) AS date,
	c.created_date,
	parts.cost_centres,
	parts.part_count > 0 AND parts.unattested_count = 0 AS attested,
	-- Branch on the type: "x IS NOT NULL" on a missing joined row is false,
	-- not NULL, so COALESCE cannot pick between the expense and invoice side.
	CASE c.type WHEN 'expense' THEN e.confirmed_by_id IS NOT NULL ELSE false END AS confirmed,
	CASE c.type WHEN 'expense' THEN e.reimbursement_id IS NOT NULL ELSE i.paid_at IS NOT NULL END AS paid,
	COALESCE(e.is_flagged, false) AS flagged,
	c.verification,
	-- Used by the predicates only: Cashflow 3's queues test the payer, not the date.
	CASE c.type WHEN 'expense' THEN e.reimbursement_id IS NOT NULL ELSE i.paid_by_id IS NOT NULL END AS paid_by_payer,
	parts.part_count,
	parts.unattested_count,
	parts.lower_ccs,
	parts.unattested_ccs
FROM core_claim c
JOIN core_profile op ON op.id = c.owner_id
JOIN auth_user u ON u.id = op.user_id
LEFT JOIN expenses_expensedata e ON e.id = c.expense_data_id
LEFT JOIN invoices_invoicedata i ON i.id = c.invoice_data_id
CROSS JOIN LATERAL (
	SELECT
		COALESCE((sum(p.amount) * 100)::bigint, 0) AS total_ore,
		count(*) AS part_count,
		count(*) FILTER (WHERE p.attested_by_id IS NULL) AS unattested_count,
		COALESCE(array_agg(DISTINCT p.cost_centre ORDER BY p.cost_centre) FILTER (WHERE p.cost_centre <> ''), '{}') AS cost_centres,
		COALESCE(array_agg(lower(p.cost_centre)), '{}') AS lower_ccs,
		COALESCE(array_agg(lower(p.cost_centre)) FILTER (WHERE p.attested_by_id IS NULL), '{}') AS unattested_ccs
	FROM core_claimpart p
	WHERE p.claim_id = c.id
) parts`

// where builds the WHERE clause for f as seen by v. ok is false when the
// viewer may not see the requested queue at all.
func where(v Viewer, f Filter) (clause string, args pgx.NamedArgs, ok bool) {
	args = pgx.NamedArgs{"me": v.Username}
	var conds []string

	// Visibility: Cashflow 3's ClaimQuerySet.viewable_by.
	if vis := v.Perms.ViewableCostCentres(); !vis.All {
		conds = append(conds, "(owner_username = @me OR lower_ccs && @view_ccs)")
		args["view_ccs"] = vis.Names
	}

	if f.Queue != "" {
		if !v.MaySeeQueue(f.Queue) {
			return "", nil, false
		}
		conds = append(conds, queueCondition(v, f.Queue, args))
	}
	if f.Mine {
		conds = append(conds, "owner_username = @me")
	}
	if f.Kind != "" {
		conds = append(conds, "kind = @kind")
		args["kind"] = string(f.Kind)
	}
	if f.CostCentre != "" {
		conds = append(conds, "@cost_centre = ANY(cost_centres)")
		args["cost_centre"] = f.CostCentre
	}
	if q := strings.TrimSpace(f.Query); q != "" {
		cond := "(description ILIKE @like ESCAPE '\\' OR owner_name ILIKE @like ESCAPE '\\' OR owner_username ILIKE @like ESCAPE '\\'"
		if n, isNumber := claimNumber(q); isNumber {
			cond += " OR number = @query_number"
			args["query_number"] = n
		}
		conds = append(conds, cond+")")
		args["like"] = "%" + escapeLike(q) + "%"
	}
	if f.ID != 0 {
		conds = append(conds, "id = @id")
		args["id"] = f.ID
	}
	if f.Number != 0 {
		conds = append(conds, "number = @number")
		args["number"] = f.Number
	}

	if len(conds) == 0 {
		return "", args, true
	}
	return "WHERE " + strings.Join(conds, " AND "), args, true
}

// queueCondition ports ClaimQuerySet's *_for methods. MaySeeQueue has
// already checked the viewer may see q.
func queueCondition(v Viewer, q Queue, args pgx.NamedArgs) string {
	switch q {
	case QueueAttest:
		// Never one's own expense (one's own invoice is fine), and only parts
		// still to attest in cost centres the viewer attests.
		cond := "NOT (kind = 'expense' AND owner_username = @me) AND "
		if ccs := v.Perms.AttestQueueCostCentres(); ccs.All {
			return cond + "unattested_count > 0"
		} else {
			args["attest_ccs"] = ccs.Names
			return cond + "unattested_ccs && @attest_ccs"
		}
	case QueueConfirm:
		return "kind = 'expense' AND NOT confirmed"
	case QueueAccount:
		cond := "verification = '' AND paid_by_payer"
		if ccs := v.Perms.AccountQueueCostCentres(); ccs.All {
			return cond
		} else {
			args["account_ccs"] = ccs.Names
			return cond + " AND lower_ccs && @account_ccs"
		}
	case QueuePay:
		return "NOT paid_by_payer AND part_count > 0 AND unattested_count = 0 AND (kind = 'invoice' OR confirmed)"
	}
	panic(fmt.Sprintf("claims: unknown queue %q", q))
}

var sortColumns = map[Sort]string{
	SortDate:        "date",
	SortAmount:      "total_ore",
	SortDescription: "lower(description)",
	SortOwner:       "lower(owner_name)",
	SortCreated:     "created_date",
}

func orderBy(f Filter) string {
	dir := "ASC"
	if f.Descending {
		dir = "DESC"
	}
	col, ok := sortColumns[f.Sort]
	if !ok {
		col = "date"
	}
	order := fmt.Sprintf("%s %s NULLS LAST, id %s", col, dir, dir)
	// Flagged expenses wait on someone; keep them out of the way in queues.
	if f.Queue != "" {
		order = "flagged, " + order
	}
	return "ORDER BY " + order
}

// List returns one page of claims matching f, and how many match in total.
func (s *Store) List(ctx context.Context, v Viewer, f Filter) ([]Summary, int, error) {
	f = f.normalise()
	clause, args, ok := where(v, f)
	if !ok {
		return nil, 0, ErrForbiddenQueue
	}

	var total int
	countSQL := "SELECT count(*) FROM (" + claimRows + ") claims " + clause
	if err := s.pool.QueryRow(ctx, countSQL, args).Scan(&total); err != nil {
		return nil, 0, fmt.Errorf("count claims: %w", err)
	}

	args["limit"] = f.PageSize
	args["offset"] = (f.Page - 1) * f.PageSize
	listSQL := "SELECT id, kind, number, description, owner_username, owner_name, total_ore, date, created_date, " +
		"cost_centres, attested, confirmed, paid, flagged, verification FROM (" + claimRows + ") claims " +
		clause + " " + orderBy(f) + " LIMIT @limit OFFSET @offset"
	rows, err := s.pool.Query(ctx, listSQL, args)
	if err != nil {
		return nil, 0, fmt.Errorf("list claims: %w", err)
	}
	summaries, err := pgx.CollectRows(rows, scanSummary)
	if err != nil {
		return nil, 0, fmt.Errorf("list claims: %w", err)
	}
	return summaries, total, nil
}

// Count returns how many claims wait in q for v.
func (s *Store) Count(ctx context.Context, v Viewer, q Queue) (int, error) {
	_, total, err := s.List(ctx, v, Filter{Queue: q, PageSize: 1})
	return total, err
}

// Get returns one claim v may view, or ErrNotFound.
func (s *Store) Get(ctx context.Context, v Viewer, kind Kind, number int64) (Summary, error) {
	return s.one(ctx, v, Filter{Kind: kind, Number: number})
}

// Visible reports whether v may view the claim with internal id claimID.
func (s *Store) Visible(ctx context.Context, v Viewer, claimID int64) (bool, error) {
	_, err := s.one(ctx, v, Filter{ID: claimID})
	if errors.Is(err, ErrNotFound) {
		return false, nil
	}
	return err == nil, err
}

func (s *Store) one(ctx context.Context, v Viewer, f Filter) (Summary, error) {
	claims, _, err := s.List(ctx, v, f)
	if err != nil {
		return Summary{}, err
	}
	if len(claims) == 0 {
		return Summary{}, ErrNotFound
	}
	return claims[0], nil
}

func scanSummary(row pgx.CollectableRow) (Summary, error) {
	var s Summary
	var kind string
	err := row.Scan(&s.ID, &kind, &s.Number, &s.Description, &s.Owner.Username, &s.Owner.Name, &s.AmountOre,
		&s.Date, &s.CreatedDate, &s.CostCentres, &s.Attested, &s.Confirmed, &s.Paid, &s.Flagged, &s.Verification)
	s.Kind = Kind(kind)
	return s, err
}

var numberPattern = regexp.MustCompile(`^#?(\d{1,15})$`)

// claimNumber recognises a search for a claim number, "1234" or "#1234".
func claimNumber(q string) (int64, bool) {
	m := numberPattern.FindStringSubmatch(q)
	if m == nil {
		return 0, false
	}
	n, err := strconv.ParseInt(m[1], 10, 64)
	return n, err == nil
}

func escapeLike(s string) string {
	return strings.NewReplacer(`\`, `\\`, `%`, `\%`, `_`, `\_`).Replace(s)
}
