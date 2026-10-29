#!/usr/bin/env bash
# Regenerates server/internal/database/cashflow3/schema.sql from Cashflow 3's
# Django migrations. Needs `make services` running (Postgres on :5433).
set -euo pipefail
cd "$(dirname "$0")/.."

db=postgres://cashflow:cashflow@localhost:5433

# The client tools must match the server's major version, so use the image's.
pg() { docker run --rm -i --network host postgres:18 "$@"; }
psql() { pg psql "$@"; }
pg_dump() { pg pg_dump "$@"; }
out=server/internal/database/cashflow3/schema.sql
header=$(sed -n '/^-- The Cashflow 3/,/^$/p' "$out")

psql -q "$db/cashflow" -c "DROP DATABASE IF EXISTS cashflow3_schema" -c "CREATE DATABASE cashflow3_schema"
docker build -q --target base -t cashflow3-base . >/dev/null
docker run --rm --network host -e DB_NAME=cashflow3_schema -e DB_HOST=localhost -e DB_PORT=5433 \
  -e SECRET_KEY=x -e OIDC_PROVIDER=http://localhost:7003 -e OIDC_ID=x -e OIDC_SECRET=x \
  cashflow3-base poetry run ./manage.py migrate -v0

clean() { grep -v '^SET \|^SELECT pg_catalog\|^--\|^\\\(un\)\?restrict' | cat -s; }
{
  echo "$header"
  echo
  pg_dump --schema-only --no-owner --no-privileges --no-comments "$db/cashflow3_schema" | clean |
    # sqlc cannot parse virtual generated columns; see the header.
    perl -0pe 's/(ELSE NULL::text\nEND\))(,\n    owner_id)/$1 STORED$2/'
  echo
  echo "-- Applied Django migrations, so Cashflow 3 can attach to a database created from this file."
  pg_dump --data-only --inserts --no-owner --no-comments -t django_migrations "$db/cashflow3_schema" | grep '^INSERT' |
    # The applied-at time is irrelevant here; now() keeps the file reproducible.
    sed -E "s/'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9:.+]+'\)/now())/"
} > "$out"

psql -q "$db/cashflow" -c "DROP DATABASE cashflow3_schema"
echo "Updated $out"
