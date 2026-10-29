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
| Database | **Shared with Cashflow 3.** Go reads and writes the Django tables through sqlc and adds only tables of its own; the schema is cleaned up in small migrations after the cutover. No migration script, no big-bang cutover (see [Database](#database)) |
| Money | Öre as integers in Go, proto and TypeScript; Django's `numeric(9,2)` amounts are converted in SQL until the cleanup. Formatting only at the edge |
| Frontend | TanStack Start in SPA mode (no SSR) + Router + Query + Form + Table, shadcn (Base UI) + Tailwind v4, Datasektionen colours/logo, light and dark, sv/en |
| Deploy | One image, one process: the Go binary embeds the built SPA and serves it next to `/api`, `/login`, `/auth/*`, `/logout`, `/fortnox/*`, `/files/*`. Fits `nomad-deploy`, which builds one image per deploy. In dev, Vite proxies those paths to Go |
| Scope | Same capabilities and permission rules as Cashflow 3; screens and flows may be reorganised. Dropping or adding features is listed and agreed separately |
| HEIC | Converted to JPEG in the browser before upload; the server accepts JPEG, PNG, WebP and PDF only. Keeps the Go build static (no cgo) |
| Upstream changes | Cashflow 3 keeps evolving on master; commits to `backend/` and `frontend/` are ported as we go, and parity tests catch drift |
| Layout | New code in `server/`, `proto/`, `web/`. Old `backend/` and `frontend/` stay until the cutover (their migrations own the schema, and parity tests read them), then get deleted |

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

Asks for D-Sys: a `cashflow_next` database restored from a production dump for staging; the SSO redirect URI `/auth/callback` for `cashflow-next` (and for `cashflow` at cutover); the new Nomad job variables.

## Database

Cashflow 4 uses Cashflow 3's database as it is. Until the cutover:

- **Django owns its tables.** Its migrations keep running from `backend/`, and Go never alters those tables. A copy of
  the schema lives in `server/internal/database/cashflow3/schema.sql` for sqlc and the dev database; `make
  django-schema` refreshes it after an upstream migration.
- **Go adds only its own tables** (e.g. `claim_events` for typed workflow history, `jobs` for the email outbox),
  through golang-migrate, recorded in `cashflow4_schema_migrations`. Django ignores tables it does not know.
- **Quirks are hidden in SQL.** Users are split over `auth_user` and `core_profile`; a claim over `core_claim` and
  `expenses_expensedata`/`invoices_invoicedata`; amounts are `numeric(9,2)`; `confirmed_by` references `auth_user`
  while `paid_by` and `attested_by` reference `core_profile`. Queries return clean rows, so none of this leaks into
  the API.
- **Users Go creates look like Django's:** an `auth_user` with an unusable password (`!`) plus a `core_profile`, as
  Django's SSO login and `post_save` signal would. Verified by running Cashflow 3 against a database Go wrote to.

Both apps can run on the same database at the same time, so the switch can happen page by page and be rolled back by
pointing Traefik back. After the cutover, Go takes over the schema and cleans it up in small, reversible migrations:
merge the claim tables, store öre, encrypt the Fortnox tokens, drop Django's auth and session tables.

## Phases

0. **Scaffold** (done): `server/` from OG-template, auth, Hive permission client, Connect wiring, the shared Django
   schema, compose (Postgres, nyckeln, dock), CI, `Dockerfile.next`, `job.next.nomad.hcl`. `web/` SPA shell with design
   tokens, i18n, the form kit, hotkeys and devtools; the profile/bank details page as the first full slice. See
   [cashflow4.md](cashflow4.md).
1. **Read path** (done): `ClaimService` (lists, the four queues, detail, queue counts, overview totals), attachments
   streamed through `/files/{id}` with a permission check, the claims table (TanStack Table, URL search params,
   debounced search, J/K keyboard navigation, mobile cards), the claim detail page, and `cmd/seed`. Budget lookups
   moved to phase 2, where the forms need them.
2. **Write path** (done): workflow actions (attest, confirm, flag, pay invoices, comment, delete) with Cashflow 3's
   comments and emails through an outbox; payouts per person and the payments list; creating and editing claims with
   GOrdian budget pickers and usage warnings, uploads (HEIC converted in the browser); rfinger profile pictures.
   Every Cashflow 3 feature and where it lands: [parity.md](parity.md).
3. **Fortnox** (done): connecting the service account (OAuth; tokens stay in Django's `fortnox_serviceaccount` and
   are refreshed under the same row lock, kept alive in the background), the booking page (voucher rows suggested
   from GOrdian accounts and Fortnox cost centres, balancing credit row, or an existing voucher number), the vouchers
   page with series filter, and a fake Fortnox (`cmd/fakefortnox`) for development and tests. Also a compactness
   pass: the main flows fit a 1366×768 laptop screen without scrolling.
4. **Stats, admin, polish**: stats/charts, user admin, i18n, accessibility, mobile.
5. **Cutover**: staging on `cashflow-next` against a production copy, then against the production database next to
   Cashflow 3; move users over page by page; switch Traefik; Go takes over the schema and starts the cleanup.
