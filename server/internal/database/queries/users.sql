-- name: UpsertUser :one
-- Creates the auth_user and core_profile rows for a first-time SSO user, as
-- Django's login and post_save signal would. An existing user is left as is:
-- Cashflow 3 keeps the SSO's given and family names, which the session lacks.
WITH inserted_user AS (
    INSERT INTO auth_user (username, first_name, last_name, email, password,
                           is_superuser, is_staff, is_active, date_joined)
    -- "!" is Django's unusable password: SSO is the only way in.
    VALUES (@username, @first_name, @last_name, @email, '!', false, false, true, now())
    ON CONFLICT (username) DO NOTHING
    RETURNING id
), target AS (
    SELECT id FROM inserted_user
    UNION ALL
    SELECT id FROM auth_user WHERE username = @username
    LIMIT 1
), inserted_profile AS (
    INSERT INTO core_profile (user_id, bank_account, sorting_number, bank_name)
    SELECT id, '', '', '' FROM target
    ON CONFLICT (user_id) DO NOTHING
)
SELECT id FROM target;

-- name: GetUser :one
-- A user is split over Django's auth_user (identity) and core_profile (bank
-- details); claims reference the profile.
SELECT u.username, u.first_name, u.last_name, u.email,
       p.id AS profile_id, p.sorting_number, p.bank_account, p.bank_name
FROM auth_user u
JOIN core_profile p ON p.user_id = u.id
WHERE u.username = @username;

-- name: UpdateBankDetails :exec
UPDATE core_profile p
SET sorting_number = @clearing_number, bank_account = @bank_account, bank_name = @bank_name
FROM auth_user u
WHERE p.user_id = u.id AND u.username = @username;

-- name: ListCostCentres :many
-- Every cost centre that appears on a claim part; permission scopes are
-- matched against these.
SELECT DISTINCT cost_centre FROM core_claimpart WHERE cost_centre <> '' ORDER BY cost_centre;
