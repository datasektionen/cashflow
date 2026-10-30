# Cashflow 4 public demo and development

Source: `datasektionen/cashflow`, branch **slop-rewrite**. The public sandbox is
https://cashflow.havet.dev, deployed from this branch by Coolify on orcy.
It contains fictional data only. Every tester shares the same database.

## Try the roles

Opening the app without a session leads to `/login`, a password-free test-user
chooser. The banner inside the app has **Byt testanvändare / Switch test user**.
The API still checks permissions through Hive on every request, using the mock
Hive service; selecting a role does not bypass workflow authorization.

| User | Permissions |
| --- | --- |
| `turetek` | Treasurer: attest, confirm, account, pay, invoices, all claims/payments, Fortnox |
| `diadat` | Attest Sektionslokalsgruppen; account every cost centre |
| `bilbek` | Account only Mottagningen 2026 |
| `sauron` | View all claims; no administrative workflow actions |
| `marmed` | Ordinary member; own expenses and invoices |
| `jobjav` | Ordinary member with missing bank details |

The database starts with expenses, invoices, comments, payments and receipts at
all workflow stages. Normal restarts and redeployments preserve them. Use only
fictional information and test receipts; demo users can see shared records.

## What is mocked

`compose.demo.yaml` runs a separate PostgreSQL database (`cashflow_demo`), S3Mock
with its own receipt volume, and `cashflow-demomocks` for Hive permissions,
GOrdian budgets, profile pictures, notification delivery and Fortnox. No emails
are sent. Fortnox connection approval and vouchers are simulated in memory;
reconnect Fortnox after restarting the mock service. No real SSO, budget,
notification or bookkeeping service is used by this stack.

Only `app:3000` gets an HTTPS route. Database, S3 and mock ports are not published.
`DEMO_MODE=true` explicitly enables demo authentication. With it disabled the
server uses its usual OIDC login, and there is no `/demo/login` handler.
Never enable it on a database containing real information.

## Development on orcy

Fleet checks out `/home/t3/dev/cashflow` for the T3 Code service account, on
`slop-rewrite`. Open the **Cashflow 4.0** T3 project on orcy. The laptop checkout
is `~/dev/cashflow`. Git commits and pushes go to the original upstream branch.

```sh
git switch slop-rewrite
git pull --ff-only
make setup        # install locked frontend dependencies
make demo         # build and start the complete local demo, localhost:5180
make demo-down    # stop it, retaining data
make demo-reset   # replace only this local demo's claims and receipts
make demo-test    # check roles, restrictions, upload, approval and mock Fortnox
```

The local stack has its own Compose project and volumes, separate from Coolify.
For hot reload use `make dev SEED=1` (the original local mock SSO setup; see
[cashflow4.md](cashflow4.md)). `make check` requires the original test database on
localhost:5433 from `make services`. Go and Bun versions are in `mise.toml`.

## Coolify deployment

Coolify project `cashflow`, application `cashflow-demo`, branch `slop-rewrite`,
build pack `dockercompose`, compose path `/compose.demo.yaml`. Route only the
`app` service to `https://cashflow.havet.dev:3000`. `PUBLIC_URL` is
`https://cashflow.havet.dev`. Coolify generates `SERVICE_PASSWORD_64_DEMOSESSION`
for the signed demo sessions (the fallback is for local development only).
DNS is a DNS-only A record to orcy, and Traefik issues the HTTPS certificate.

After pushing a commit, deploy this application in Coolify. It builds
`Dockerfile.demo`, waits for the database, S3 and mock services, applies migrations,
and seeds only an empty database. It refuses to seed arbitrary remote databases;
only localhost or the explicitly enabled `demo-db/cashflow_demo` target is allowed.

To reset the hosted sandbox, use the application's terminal on the **app**
container and run `cashflow-seed -reset`. This replaces demo claims, receipts and
payments for all testers. Normal deploys never reset data automatically.
`cashflow-verify` reads every claim and checks its receipt in S3 without changes.

Run the same smoke checks against the hosted sandbox with
`CASHFLOW_DEMO_URL=https://cashflow.havet.dev make demo-test`. The workflow check
adds one clearly named demo expense without resetting other testers' data.
