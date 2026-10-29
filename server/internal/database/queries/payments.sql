-- name: InsertPayment :one
INSERT INTO expenses_payment (date, payer_id, receiver_id) VALUES (@on_date, @payer_id, @receiver_id) RETURNING id;

-- name: SetReimbursement :exec
UPDATE expenses_expensedata SET reimbursement_id = @payment_id WHERE id = @id;

-- name: ListPayments :many
-- Payments, newest first, optionally only those whose tag ("Data" || id)
-- contains @tag, as Cashflow 3's payments list.
SELECT pay.id, pay.date,
       pu.username AS payer_username, trim(pu.first_name || ' ' || pu.last_name)::text AS payer_name,
       ru.username AS receiver_username, trim(ru.first_name || ' ' || ru.last_name)::text AS receiver_name,
       (SELECT COALESCE((sum(p.amount) * 100)::bigint, 0) FROM core_claimpart p
          JOIN core_claim c ON c.id = p.claim_id JOIN expenses_expensedata e ON e.id = c.expense_data_id
          WHERE e.reimbursement_id = pay.id)::bigint AS total_ore,
       (SELECT count(*) FROM expenses_expensedata e WHERE e.reimbursement_id = pay.id)::int AS expense_count,
       count(*) OVER ()::int AS total_count
FROM expenses_payment pay
JOIN core_profile pp ON pp.id = pay.payer_id JOIN auth_user pu ON pu.id = pp.user_id
JOIN core_profile rp ON rp.id = pay.receiver_id JOIN auth_user ru ON ru.id = rp.user_id
WHERE @tag::text = '' OR ('Data' || pay.id) ILIKE '%' || @tag::text || '%'
ORDER BY pay.date DESC, pay.id DESC
LIMIT @lim OFFSET @off;

-- name: ListPaymentExpenses :many
SELECT e.id AS number FROM expenses_expensedata e WHERE e.reimbursement_id = @payment_id ORDER BY e.id;
