#!/usr/bin/env bash
# Checks that Cashflow 3 and 4 can share one database, as they will during
# the cutover. Against the dev services (make services), with some claims
# made in Cashflow 4 (make dev-server, or go run ./cmd/seed):
#
#   1. Cashflow 3 writes a claim through its own models and storage.
#   2. Cashflow 4 reads every claim and finds every file (cmd/verify).
#   3. Cashflow 3 reads every claim through its API serializers, and fetches
#      every file through its storage, Cashflow 4's uploads included.
set -euo pipefail
cd "$(dirname "$0")/.."

docker build -q --target base -t cashflow3-base . >/dev/null
django() {
  docker run --rm --network host -v "$PWD/scripts/coexistence:/check:ro" -e PYTHONPATH=/app \
    -e DB_HOST=localhost -e DB_PORT=5433 -e DEBUG=True -e DJANGO_LOG_LEVEL=WARNING -e SECRET_KEY=x \
    -e OIDC_PROVIDER=http://localhost:7003 -e OIDC_ID=x -e OIDC_SECRET=x \
    -e S3_HOST=http://localhost:9091 -e S3_ACCESS_KEY_ID=dev -e S3_SECRET_ACCESS_KEY=dev \
    -e HIVE_URL=http://localhost:7004 -e HIVE_SECRET=dev \
    cashflow3-base poetry run python "$@"
}

echo "== Cashflow 3 writes"
django /check/write.py
echo "== Cashflow 4 reads"
(cd server && go run ./cmd/verify)
echo "== Cashflow 3 reads"
django /check/check.py
