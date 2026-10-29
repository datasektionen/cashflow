-- Statistics, ported from Cashflow 3's stats app. Visible to everyone.

-- name: MonthlyStats :many
-- Claims and their totals per month of a year, by expense date for expenses
-- and invoice date for invoices.
SELECT c.type::text AS kind,
       extract(month FROM COALESCE(e.expense_date, i.invoice_date))::int AS month,
       count(DISTINCT c.id)::int AS claims,
       COALESCE((sum(p.amount) * 100)::bigint, 0)::bigint AS total_ore
FROM core_claim c
LEFT JOIN expenses_expensedata e ON e.id = c.expense_data_id
LEFT JOIN invoices_invoicedata i ON i.id = c.invoice_data_id
LEFT JOIN core_claimpart p ON p.claim_id = c.id
WHERE COALESCE(e.expense_date, i.invoice_date) >= @from_date::date
  AND COALESCE(e.expense_date, i.invoice_date) < @to_date::date
GROUP BY 1, 2;

-- name: ExpenseTotalsByOwner :many
-- Everyone's expenses dated @from_date or later. capped_total_ore leaves out
-- expenses of 10 000 kr or more, so one large purchase cannot top the
-- leaderboard (Cashflow 3's capped_expenses); total_ore counts everything.
WITH expenses AS (
    SELECT c.owner_id, COALESCE(sum(p.amount), 0) AS total
    FROM core_claim c
    JOIN expenses_expensedata e ON e.id = c.expense_data_id
    LEFT JOIN core_claimpart p ON p.claim_id = c.id
    WHERE e.expense_date >= @from_date::date
    GROUP BY c.id, c.owner_id
)
SELECT u.username,
       trim(u.first_name || ' ' || u.last_name)::text AS name,
       COALESCE((sum(x.total) FILTER (WHERE x.total > 0 AND x.total < 10000) * 100)::bigint, 0)::bigint AS capped_total_ore,
       (sum(x.total) * 100)::bigint AS total_ore,
       count(*)::int AS expenses
FROM expenses x
JOIN core_profile op ON op.id = x.owner_id
JOIN auth_user u ON u.id = op.user_id
GROUP BY u.username, u.first_name, u.last_name;

-- name: SearchUsers :many
-- Users by username or name, for the admin user list.
SELECT u.username, trim(u.first_name || ' ' || u.last_name)::text AS name, u.email
FROM auth_user u
JOIN core_profile p ON p.user_id = u.id
WHERE @query::text = ''
   OR u.username ILIKE '%' || @query::text || '%'
   OR (u.first_name || ' ' || u.last_name) ILIKE '%' || @query::text || '%'
ORDER BY u.first_name, u.last_name, u.username
LIMIT 50;
