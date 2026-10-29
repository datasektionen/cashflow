-- Creating and editing claims, run in a transaction by claims.Store.

-- name: InsertUpload :exec
INSERT INTO cashflow4_uploads (id, uploader, storage_key, filename, content_type, size_bytes)
VALUES (@id, @uploader, @storage_key, @filename, @content_type, @size_bytes);

-- name: TakeUploads :many
-- The caller's unattached uploads among @ids, marked attached in the same step.
UPDATE cashflow4_uploads SET attached_at = now()
WHERE id = ANY(@ids::text[]) AND uploader = @uploader AND attached_at IS NULL
RETURNING id, storage_key;

-- name: InsertExpenseData :one
INSERT INTO expenses_expensedata (expense_date, is_flagged) VALUES (@expense_date, false) RETURNING id;

-- name: InsertInvoiceData :one
INSERT INTO invoices_invoicedata (invoice_date, invoice_number, due_date)
VALUES (sqlc.narg(invoice_date), @invoice_number, sqlc.narg(due_date)) RETURNING id;

-- name: InsertClaim :one
INSERT INTO core_claim (description, created_date, verification, expense_data_id, invoice_data_id, owner_id)
VALUES (@description, @created_date, '', sqlc.narg(expense_data_id), sqlc.narg(invoice_data_id), @owner_id)
RETURNING id;

-- name: InsertPart :exec
INSERT INTO core_claimpart (claim_id, cost_centre, secondary_cost_centre, budget_line, amount)
VALUES (@claim_id, @cost_centre, @secondary_cost_centre, @budget_line, sqlc.arg(amount_ore)::bigint::numeric / 100);

-- name: InsertFile :exec
INSERT INTO core_file (claim_id, file) VALUES (@claim_id, @file);

-- name: ListPartsForEdit :many
SELECT cost_centre, secondary_cost_centre, budget_line, (amount * 100)::bigint AS amount_ore
FROM core_claimpart WHERE claim_id = @claim_id ORDER BY id;

-- name: UpdateClaimDescription :exec
UPDATE core_claim SET description = @description WHERE id = @id;

-- name: UpdateExpenseDate :exec
-- Editing an expense also clears its flag, as in Cashflow 3.
UPDATE expenses_expensedata SET expense_date = @expense_date, is_flagged = false WHERE id = @id;

-- name: UpdateInvoiceData :exec
UPDATE invoices_invoicedata SET invoice_date = sqlc.narg(invoice_date), invoice_number = @invoice_number, due_date = sqlc.narg(due_date)
WHERE id = @id;

-- name: DeleteFiles :execrows
DELETE FROM core_file WHERE claim_id = @claim_id AND id = ANY(@ids::bigint[]);

-- name: ResetConfirmation :exec
UPDATE expenses_expensedata SET confirmed_by_id = NULL, confirmed_at = NULL WHERE id = @id;

-- name: BudgetUsage :many
-- Amounts per budget line between two dates (a year), by Cashflow 3's effective date
-- (expense date, else invoice date, else payment date), names normalised
-- as budget/api/views.py does. @exclude_claim_id leaves out the claim being edited.
SELECT lower(regexp_replace(trim(p.cost_centre), '\s+', ' ', 'g'))::text AS cost_centre,
       lower(regexp_replace(trim(p.secondary_cost_centre), '\s+', ' ', 'g'))::text AS secondary_cost_centre,
       lower(regexp_replace(trim(p.budget_line), '\s+', ' ', 'g'))::text AS budget_line,
       COALESCE((sum(p.amount) * 100)::bigint, 0)::bigint AS uploaded_ore,
       COALESCE((sum(p.amount) FILTER (WHERE p.attested_by_id IS NOT NULL) * 100)::bigint, 0)::bigint AS attested_ore,
       COALESCE((sum(p.amount) FILTER (WHERE e.reimbursement_id IS NOT NULL OR i.paid_at IS NOT NULL) * 100)::bigint, 0)::bigint AS paid_ore
FROM core_claimpart p
JOIN core_claim c ON c.id = p.claim_id
LEFT JOIN expenses_expensedata e ON e.id = c.expense_data_id
LEFT JOIN invoices_invoicedata i ON i.id = c.invoice_data_id
WHERE COALESCE(e.expense_date, i.invoice_date, i.paid_at) >= @from_date::date
  AND COALESCE(e.expense_date, i.invoice_date, i.paid_at) < @to_date::date
  AND c.id <> @exclude_claim_id
GROUP BY 1, 2, 3;
