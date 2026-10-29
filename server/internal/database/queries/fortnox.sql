-- The Fortnox service account's OAuth tokens. Cashflow 3 keeps them in
-- fortnox_serviceaccount, one row at most, and both apps refresh them under
-- the same row lock while they share the database: Fortnox rotates the
-- refresh token on every refresh, so they must never keep separate copies.

-- name: LockFortnoxTokens :one
SELECT id, access_token, refresh_token, expires_at
FROM fortnox_serviceaccount
ORDER BY id
LIMIT 1
FOR UPDATE;

-- name: UpdateFortnoxTokens :exec
UPDATE fortnox_serviceaccount
SET access_token = @access_token, refresh_token = @refresh_token, expires_at = @expires_at
WHERE id = @id;

-- name: DeleteFortnoxTokens :exec
DELETE FROM fortnox_serviceaccount;

-- name: InsertFortnoxTokens :exec
INSERT INTO fortnox_serviceaccount (authenticated_by_id, created_at, access_token, refresh_token, expires_at)
SELECT u.id, now(), @access_token, @refresh_token, @expires_at
FROM auth_user u
WHERE u.username = @username;

-- name: GetFortnoxConnection :one
SELECT s.created_at, s.expires_at, u.username,
       trim(u.first_name || ' ' || u.last_name)::text AS name
FROM fortnox_serviceaccount s
JOIN auth_user u ON u.id = s.authenticated_by_id
ORDER BY s.id
LIMIT 1;

-- name: ListVerificationSeries :many
-- The voucher series letters used by accounted claims, for series that are
-- no longer in Fortnox.
SELECT DISTINCT upper(left(verification, 1))::text AS code
FROM core_claim
WHERE verification ~ '^[A-Za-z]'
ORDER BY code;

-- name: SetVerification :exec
UPDATE core_claim SET verification = @verification WHERE id = @id;

-- name: GetVoucherDetails :one
-- What a voucher needs from a claim: its total and transaction date (the
-- expense date, or the invoice date).
SELECT COALESCE((SELECT sum(amount) FROM core_claimpart WHERE claim_id = c.id) * 100, 0)::bigint AS total_ore,
       COALESCE(e.expense_date, i.invoice_date) AS date
FROM core_claim c
LEFT JOIN expenses_expensedata e ON e.id = c.expense_data_id
LEFT JOIN invoices_invoicedata i ON i.id = c.invoice_data_id
WHERE c.id = @id;
