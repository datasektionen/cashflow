-- Detail queries for one claim, by core_claim.id. Callers check visibility
-- first (claims.Store.Get). Amounts are converted to öre here.

-- name: ListClaimParts :many
SELECT p.id, p.cost_centre, p.secondary_cost_centre, p.budget_line,
       (p.amount * 100)::bigint AS amount_ore,
       COALESCE(u.username, '') AS attested_by_username,
       COALESCE(trim(u.first_name || ' ' || u.last_name), '')::text AS attested_by_name,
       p.attest_date
FROM core_claimpart p
LEFT JOIN core_profile ap ON ap.id = p.attested_by_id
LEFT JOIN auth_user u ON u.id = ap.user_id
WHERE p.claim_id = @claim_id
ORDER BY p.id;

-- name: ListClaimFiles :many
SELECT id, file FROM core_file WHERE claim_id = @claim_id ORDER BY id;

-- name: ListClaimComments :many
SELECT u.username AS author_username, trim(u.first_name || ' ' || u.last_name) AS author_name,
       c.content, c.date
FROM core_comment c
JOIN core_profile ap ON ap.id = c.author_id
JOIN auth_user u ON u.id = ap.user_id
WHERE c.claim_id = @claim_id
ORDER BY c.date, c.id;

-- name: GetExpenseDetails :one
-- confirmed_by references auth_user, unlike the profile references elsewhere.
SELECT COALESCE(cu.username, '') AS confirmed_by_username,
       COALESCE(trim(cu.first_name || ' ' || cu.last_name), '')::text AS confirmed_by_name,
       e.confirmed_at,
       pay.id AS payment_id,
       pay.date AS payment_date,
       COALESCE(pu.username, '') AS payer_username,
       COALESCE(trim(pu.first_name || ' ' || pu.last_name), '')::text AS payer_name
FROM core_claim c
JOIN expenses_expensedata e ON e.id = c.expense_data_id
LEFT JOIN auth_user cu ON cu.id = e.confirmed_by_id
LEFT JOIN expenses_payment pay ON pay.id = e.reimbursement_id
LEFT JOIN core_profile pp ON pp.id = pay.payer_id
LEFT JOIN auth_user pu ON pu.id = pp.user_id
WHERE c.id = @claim_id;

-- name: GetInvoiceDetails :one
SELECT i.invoice_number, i.due_date, i.paid_at,
       COALESCE(u.username, '') AS paid_by_username,
       COALESCE(trim(u.first_name || ' ' || u.last_name), '')::text AS paid_by_name
FROM core_claim c
JOIN invoices_invoicedata i ON i.id = c.invoice_data_id
LEFT JOIN core_profile pp ON pp.id = i.paid_by_id
LEFT JOIN auth_user u ON u.id = pp.user_id
WHERE c.id = @claim_id;

-- name: GetFile :one
SELECT id, claim_id, file FROM core_file WHERE id = @id;

-- name: GetOverview :one
-- Totals of the user's own claims. "Awaiting payment" follows the pay queue:
-- every part attested and, for expenses, the receipt confirmed.
WITH mine AS (
    SELECT c.id,
           -- Branch on the type; see claimRows in internal/claims/store.go.
           CASE c.type WHEN 'expense' THEN e.reimbursement_id IS NOT NULL ELSE i.paid_by_id IS NOT NULL END AS paid,
           CASE c.type WHEN 'expense' THEN e.confirmed_by_id IS NOT NULL ELSE true END AS confirmed_or_invoice,
           COALESCE(pay.date, i.paid_at) AS paid_date,
           (SELECT COALESCE((sum(p.amount) * 100)::bigint, 0) FROM core_claimpart p WHERE p.claim_id = c.id) AS total_ore,
           EXISTS (SELECT 1 FROM core_claimpart p WHERE p.claim_id = c.id AND p.attested_by_id IS NULL) AS has_unattested
    FROM core_claim c
    JOIN core_profile op ON op.id = c.owner_id
    JOIN auth_user u ON u.id = op.user_id
    LEFT JOIN expenses_expensedata e ON e.id = c.expense_data_id
    LEFT JOIN expenses_payment pay ON pay.id = e.reimbursement_id
    LEFT JOIN invoices_invoicedata i ON i.id = c.invoice_data_id
    WHERE u.username = @username
)
SELECT
    COALESCE(sum(total_ore) FILTER (WHERE NOT paid AND has_unattested), 0)::bigint AS awaiting_attest_ore,
    COALESCE(sum(total_ore) FILTER (WHERE NOT paid AND NOT has_unattested AND confirmed_or_invoice), 0)::bigint AS awaiting_payment_ore,
    COALESCE(sum(total_ore) FILTER (WHERE paid AND paid_date >= date_trunc('year', now())), 0)::bigint AS paid_this_year_ore
FROM mine;
