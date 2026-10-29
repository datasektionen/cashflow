# Go-owned migrations

Until the cutover, the database is shared with Cashflow 3 and Django owns its
tables (see `../cashflow3/schema.sql`). Migrations here may only create tables
that Django does not know about, such as `claim_events` or `jobs`. They are
recorded in `cashflow4_schema_migrations`, separate from `django_migrations`.

Add a pair `00000N_<name>.up.sql` / `.down.sql`; the server applies new ones on
startup. Never edit a migration that has been deployed.
