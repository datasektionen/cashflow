# Cashflow 4.0: Go + TanStack Start rewrite

Branch: `slop-rewrite`. Upstream rewrite, agreed with the maintainers.

## Goals

- Replace the Django backend with Go and the SvelteKit frontend with TanStack Start (React).
- Completely redesign the UI: clear workflows (submit → attest → confirm → account → pay), fast, good on mobile.
- Keep feature parity and all production data; keep deploying to Datasektionen's Nomad cluster.

## Decisions

| Topic | Decision |
|---|---|
| Go skeleton | [`OG-template`](https://github.com/datasektionen/OG-template) layout: stdlib `net/http` mux, slog, graceful shutdown, Alpine Dockerfile, `job.nomad.hcl` |
| Login / session | [`GO-auth-yourself`](https://github.com/datasektionen/GO-auth-yourself): `/login`, `/auth/callback`, `/logout`, signed session cookie (2-day duration, as today) |
| Permissions | Live Hive lookup (`/api/v1/user/:id/permissions`, bearer token) with a 60 s per-user cache; exact port of `cashflow/dauth.py`. Permissions in the session cookie are ignored |
| API | ConnectRPC (same setup as quoteams): protos in `proto/`, `buf` via bun, `protoc-gen-go` + `protoc-gen-connect-go` via `go tool`, `protoc-gen-es` + `connect-query` for the frontend. Plain HTTP routes only for uploads/downloads and OAuth callbacks |
| API auth | Connect interceptor returns `Unauthenticated`/`PermissionDenied`; never the library's 302 redirect for API calls |
| Database | **New schema** (Postgres, pgx + sqlc, golang-migrate embedded in the binary) and a one-time migration script from the Django schema; hard cutover |
| Money | `bigint` öre everywhere (DB, proto, TS). Formatting only at the edge |
| Frontend | TanStack Start in SPA mode (no SSR) + Router + Query + Form + Table, shadcn (Base UI) + Tailwind v4, Datasektionen colours/logo, light and dark, sv/en |
| Deploy | One image, one process: the Go binary embeds the built SPA and serves it next to `/api`, `/login`, `/auth/*`, `/logout`, `/fortnox/*`, `/files/*`. Fits `nomad-deploy`, which builds one image per deploy. In dev, Vite proxies those paths to Go |
| Scope | Same capabilities and permission rules as Cashflow 3; screens and flows may be reorganised. Dropping or adding features is listed and agreed separately |
| HEIC | Converted to JPEG in the browser before upload; the server accepts JPEG, PNG, WebP and PDF only. Keeps the Go build static (no cgo) |
| Upstream changes | Cashflow 3 keeps evolving on master; commits to `backend/` and `frontend/` are ported as we go, and parity tests catch drift |
| Layout | New code in `server/`, `proto/`, `web/`. Old `backend/` and `frontend/` stay until cutover (the migration script and parity tests read them), then get deleted |

## Datasektionen dependencies

| System | Used for | Local mock |
|---|---|---|
| SSO `sso.datasektionen.se/op` | OIDC login | nyckeln-under-dorrmattan |
| Hive | permissions (scoped by cost centre) | nyckeln (accepts any token) |
| GOrdian `budget.datasektionen.se` | cost centres, secondary cost centres, budget lines | GOrdian itself in compose or recorded fixtures |
| rfinger | profile pictures | dock |
| spam | email notifications | dock |
| S3 bucket `dsekt-cashflow-2` | receipts and invoices | minio |
| Fortnox | OAuth, accounts, cost centres, vouchers | recorded fixtures |

Asks for D-Sys before cutover: change the SSO redirect URI from `/oidc/callback` to `/auth/callback`; add the new Nomad job variables.

## New schema (draft)

```
users            username PK (KTH id), name, email, bank_account, clearing_number, bank_name, created_at
claims           id PK, kind ('expense'|'invoice'), number (public id, unique per kind), owner → users,
                 description, created_at, verification,
                 -- expense: expense_date, confirmed_by → users, confirmed_at, payment_id → payments, flagged
                 -- invoice: invoice_number, invoice_date, due_date, paid_by → users, paid_at
                 CHECK constraints per kind
claim_parts      id, claim_id, position, cost_centre, secondary_cost_centre, budget_line, amount_ore bigint,
                 attested_by → users, attested_at
claim_files      id, claim_id, storage_key, filename, content_type, size_bytes, page_count, created_at
comments         id, claim_id, author → users, body, created_at
claim_events     id, claim_id, actor → users, type (attested, unattested, confirmed, unconfirmed, accounted,
                 paid, flagged, …), part_id?, data jsonb, created_at   -- replaces the Swedish "system comments"
payments         id, payer → users, receiver → users, created_at   (tag = "Data" || id)
fortnox_account  singleton; access/refresh token encrypted at rest (AES-GCM with APP key), expires_at, authenticated_by
jobs             outbox for emails and retries: kind, payload jsonb, run_at, attempts, last_error
```

`number` keeps the old `expense_data.id` / `invoice_data.id`, so old links and the `(id) description` text in Fortnox
vouchers stay valid. Expenses and invoices have separate number sequences, as today.

The migration script copies `auth_user` + `core_profile` → `users`; `core_claim` + `expenses_expensedata` /
`invoices_invoicedata` → `claims`; parts, files, comments and payments one to one; Fortnox tokens re-encrypted. Old
system comments ("Attesterar kvittodelen …") are kept as comments; new actions write `claim_events`. The script
verifies row counts and amount totals per claim, and runs repeatedly against a production dump before cutover.

## Phases

0. **Scaffold** (done): `server/` from OG-template, auth, Hive permission client, Connect wiring, schema migration,
   compose (Postgres, nyckeln, dock), CI, `Dockerfile.next`, `job.next.nomad.hcl`. `web/` SPA shell with design
   tokens, i18n, the form kit, hotkeys and devtools; the profile/bank details page as the first full slice. See
   [cashflow4.md](cashflow4.md).
1. **Read path**: claims list/detail, files, budget lookups, the action queues (attest, confirm, account, pay).
   Brings the shared TanStack Table setup and Pacer (debounced search).
2. **Write path**: create/edit expenses and invoices, uploads (HEIC → JPEG), comments, attest/confirm/pay with undo,
   emails through the outbox. Brings minio and mailpit into `compose.next.yaml`.
3. **Fortnox**: OAuth, accounting views, voucher creation, with parity tests against the Python implementation.
4. **Stats, admin, polish**: stats/charts, user admin, i18n, accessibility, mobile.
5. **Migration and cutover**: script hardened against production dumps, staging on `cashflow-next`, freeze, migrate,
   switch Traefik.
