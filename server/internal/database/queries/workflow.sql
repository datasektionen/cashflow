-- Workflow changes, run in a transaction by claims.Store. Rows are locked
-- with FOR UPDATE so two attesters cannot race on the same claim.

-- name: GetActor :one
-- The profile and auth_user ids behind a username, for writing changes.
SELECT p.id AS profile_id, u.id AS user_id
FROM auth_user u JOIN core_profile p ON p.user_id = u.id
WHERE u.username = @username;

-- name: LockClaim :one
SELECT c.id, c.type, c.description, c.verification, c.expense_data_id, c.invoice_data_id, c.owner_id,
       e.is_flagged, e.confirmed_by_id, e.reimbursement_id, i.paid_by_id, i.paid_at
FROM core_claim c
LEFT JOIN expenses_expensedata e ON e.id = c.expense_data_id
LEFT JOIN invoices_invoicedata i ON i.id = c.invoice_data_id
WHERE c.id = @id
FOR UPDATE OF c;

-- name: LockPart :one
SELECT id, claim_id, cost_centre, budget_line, (amount * 100)::bigint AS amount_ore, attested_by_id
FROM core_claimpart
WHERE id = @id
FOR UPDATE;

-- name: ListPartStates :many
SELECT id, cost_centre, (attested_by_id IS NOT NULL)::boolean AS attested
FROM core_claimpart WHERE claim_id = @claim_id ORDER BY id;

-- name: SetPartAttestation :exec
UPDATE core_claimpart SET attested_by_id = sqlc.narg(profile_id), attest_date = sqlc.narg(on_date) WHERE id = @id;

-- name: SetConfirmation :exec
-- confirmed_by references auth_user, not core_profile.
UPDATE expenses_expensedata SET confirmed_by_id = sqlc.narg(user_id), confirmed_at = sqlc.narg(on_date) WHERE id = @id;

-- name: SetFlagged :exec
UPDATE expenses_expensedata SET is_flagged = @flagged WHERE id = @id;

-- name: SetInvoicePaid :exec
UPDATE invoices_invoicedata SET paid_by_id = @profile_id, paid_at = @on_date WHERE id = @id;

-- name: InsertComment :exec
INSERT INTO core_comment (claim_id, author_id, content, date) VALUES (@claim_id, @author_id, @content, now());

-- name: GetCommentRecipient :one
-- The claim owner, who is emailed about new comments.
SELECT u.username, u.email, trim(u.first_name || ' ' || u.last_name)::text AS name
FROM core_claim c JOIN core_profile p ON p.id = c.owner_id JOIN auth_user u ON u.id = p.user_id
WHERE c.id = @claim_id;

-- name: GetPersonName :one
SELECT trim(u.first_name || ' ' || u.last_name)::text AS name FROM auth_user u WHERE u.username = @username;

-- Deleting a claim. Django deletes children in Python, so the foreign keys
-- have no ON DELETE CASCADE and each table is cleared explicitly.

-- name: DeleteClaimComments :exec
DELETE FROM core_comment WHERE claim_id = @claim_id;

-- name: DeleteClaimFiles :exec
DELETE FROM core_file WHERE claim_id = @claim_id;

-- name: DeleteClaimParts :exec
DELETE FROM core_claimpart WHERE claim_id = @claim_id;

-- name: DeleteClaim :exec
DELETE FROM core_claim WHERE id = @id;

-- name: DeleteExpenseData :exec
DELETE FROM expenses_expensedata WHERE id = @id;

-- name: DeleteInvoiceData :exec
DELETE FROM invoices_invoicedata WHERE id = @id;

-- name: EnqueueEmail :exec
INSERT INTO cashflow4_outbox (payload) VALUES (@payload);

-- name: ClaimDueEmails :many
-- Up to 10 due emails, locked so that two servers never send the same one.
SELECT id, payload, attempts FROM cashflow4_outbox
WHERE sent_at IS NULL AND run_at <= now() AND attempts < @max_attempts
ORDER BY run_at
LIMIT 10
FOR UPDATE SKIP LOCKED;

-- name: MarkEmailSent :exec
UPDATE cashflow4_outbox SET sent_at = now(), attempts = attempts + 1 WHERE id = @id;

-- name: MarkEmailFailed :exec
UPDATE cashflow4_outbox SET attempts = attempts + 1, last_error = @last_error, run_at = @retry_at WHERE id = @id;
