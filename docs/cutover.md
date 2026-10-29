# Cutover: Cashflow 3 → Cashflow 4

How Cashflow 4 takes over from Cashflow 3 with nothing lost and a way back at every step. The order matters: each step
is checked before the next, and until the last one Cashflow 3 keeps working as today.

What is ready (checked locally, `make check`, `make build`, `make coexistence`):

- **The production image** (`Dockerfile.next`): one binary that serves the app, plus `cashflow-verify`.
- **One database for both apps:**
  - Each app reads what the other writes. `make coexistence` checks this in both directions, files included.
  - Cashflow 4 only adds tables named `cashflow4_*`, which Django ignores.
- **Old links:** Cashflow 3's addresses redirect permanently. That covers comment emails (`/<user>/expenses/<id>`), `/admin/...` and `/budget/<id>`.
- **The staging job** `job.next.nomad.hcl`, for `cashflow-next.datasektionen.se`.

## What D-Sys needs to do

1. **A database for staging:** `cashflow_next` on the production Postgres, restored from a dump of `cashflow`, with
   its own user.
2. **Nomad variables** at `nomad/jobs/cashflow-next`:
   - `db_password`
   - `app_secret_key`: 64+ random characters; it signs the session cookie.
   - `oidc_secret`
   - `hive_api_token_secret`
   - `s3_access_key_id` and `s3_secret_access_key`: the same bucket as Cashflow 3. Read access is enough for staging;
     uploads need write access.
   - `rfinger_api_key`
3. **SSO:** register the redirect URL `https://cashflow-next.datasektionen.se/auth/callback` for the `cashflow` client.
   At the switch, also register `https://cashflow.datasektionen.se/auth/callback`.
4. **Fortnox** (step 3 below): register the redirect URL `https://cashflow-next.datasektionen.se/fortnox/auth/complete`.
   At the switch, also register `https://cashflow.datasektionen.se/fortnox/auth/complete`.
5. **Hive:** nothing. Cashflow 4 uses the same `cashflow` system and permissions.

## 1. Staging on a copy of production

Deploy `job.next.nomad.hcl` against `cashflow_next`, then run, in the allocation:

```console
$ /bin/cashflow-verify
```

It reads every claim the way the pages do and checks each receipt is in S3, without writing anything (its database
connection is read-only). It must end with `0 problems`. Anything it lists is data that Cashflow 4 would show wrongly.

Then try every page as real people with their real permissions. Two things stay off on purpose. The job file explains why:

- **Emails** (no `SPAM_API_KEY`): the copy holds real addresses. Emails are logged instead of sent.
- **Fortnox** (no `FORTNOX_*`): the copy holds a copy of production's Fortnox tokens. Fortnox issues a new refresh
  token on every refresh, so staging refreshing its copy would disconnect production Cashflow 3. Booking can still be
  tried by entering voucher numbers.

The copy can be thrown away and restored again at any time.

## 2. Staging on the production database, beside Cashflow 3

Point `DATABASE_URL` at `cashflow` (Cashflow 3's database and user) and redeploy. Cashflow 4's migrations run on start
and only create `cashflow4_outbox`, `cashflow4_uploads` and `cashflow4_schema_migrations`.

Now both apps work on the same data, and people can use either. Each sends the emails for its own actions, so nobody
is emailed twice.

Cashflow 4 locks a claim's row for every workflow step, but Cashflow 3 only does so when booking. Its payouts, for one,
check and write without a lock, so the same expense paid out in both apps at the same moment could be paid twice.
**While both run, the treasurer pays out in Cashflow 4 only.** Attesting and confirming the same claim in both apps
at once is harmless: the second step just finds the work done.

While both run:

- **No Django migrations.** Cashflow 3 runs `manage.py migrate` every time it starts. A migration that changes a
  table Cashflow 4 reads needs `make django-schema`, `make gen` and a new Cashflow 4 deploy first. CI fails on a schema
  that drifts.
- **Add `SPAM_API_KEY`** to the staging variables and template, so Cashflow 4's emails are sent.

## 3. Fortnox on Cashflow 4

On the production database both apps share the single token row in `fortnox_serviceaccount`, refreshed under the same
row lock, so they cannot disconnect each other. Add `FORTNOX_CLIENT_ID` and `FORTNOX_CLIENT_SECRET`, the same as
Cashflow 3's, to the staging variables, and register the redirect URL (D-Sys item 4).

Fortnox is already connected through Cashflow 3, so nothing needs reconnecting. Cashflow 4 refreshes the tokens before
they expire, which also keeps Cashflow 3 connected. (Cashflow 3's `refresh_fortnox_token` command is not scheduled
anywhere in this repository.)

Book one claim on staging and check the voucher in Fortnox: series E for expenses (U for invoices), the text
`(<number>) <description>`, the date, and the rows.

## 4. The switch

1. In `job.next.nomad.hcl`:
   - Change the host to `cashflow.datasektionen.se`, and update `PUBLIC_URL` and `OIDC_REDIRECT_URL` to match.
   - Rename the job to `cashflow`.
   - Move the variables to `nomad/jobs/cashflow`.
2. Replace `job.nomad.hcl` and `Dockerfile` with the `.next` files, and point `deploy.yml` at them.
3. Stop the old `cashflow` job and deploy the new one.

Old bookmarks and email links redirect. Nothing in the data changes, so a rollback is a redeploy of the old job: Cashflow
3 reads everything Cashflow 4 wrote.

## 5. After the switch

Once Cashflow 3 is gone for good, Cashflow 4 owns the schema and cleans it up in small, reversible migrations (see
[rewrite-plan.md](rewrite-plan.md#database)):

- merge the claim tables
- store öre instead of `numeric(9, 2)`
- encrypt the Fortnox tokens
- drop Django's auth and session tables and `django_migrations`

Delete `backend/`, `frontend/`, the Cashflow 3 compose file and `scripts/django-schema.sh`. Also delete the
`cashflow3/schema.sql` snapshot, once the migrations own the schema.

## Rolling back

| From | Back to Cashflow 3 |
|---|---|
| Staging on a copy | Nothing to do: production was never touched. |
| Staging on production | Stop `cashflow-next`. What people did there is in the shared tables and shows in Cashflow 3. |
| After the switch | Redeploy the old `cashflow` job and its Traefik rule. Same as above. |
| After the cleanup migrations | Not possible: start the cleanup only once Cashflow 3 is retired. |
