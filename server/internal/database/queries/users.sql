-- name: UpsertUser :one
-- Called on authenticated requests so every SSO user has a row; keeps name and
-- email in sync with the SSO without touching bank details.
INSERT INTO users (username, name, email)
VALUES ($1, $2, $3)
ON CONFLICT (username) DO UPDATE
SET name = EXCLUDED.name, email = EXCLUDED.email
RETURNING *;

-- name: GetUser :one
SELECT * FROM users WHERE username = $1;

-- name: ListCostCentres :many
-- Every cost centre that appears on a claim part; permission scopes are
-- matched against these.
SELECT DISTINCT cost_centre FROM claim_parts WHERE cost_centre <> '' ORDER BY cost_centre;

-- name: UpdateBankDetails :one
UPDATE users
SET clearing_number = $2, bank_account = $3, bank_name = $4
WHERE username = $1
RETURNING *;
