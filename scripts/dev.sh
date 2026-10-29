#!/usr/bin/env bash
# Everything for local development in one terminal: the mock services
# (Postgres, SSO, Hive, rfinger, spam, S3), a fake Fortnox, the Go server and
# the web app. Output is prefixed per process; Ctrl-C stops them all.
#
#   make dev            # then open http://localhost:5173 and log in as turetek
#   make dev SEED=1     # first fill the database with claims at every stage
set -euo pipefail
cd "$(dirname "$0")/.."

[[ -f server/.env ]] || { cp server/.env.example server/.env; echo "Created server/.env from .env.example"; }
[[ -d web/node_modules ]] || (cd web && bun install)

docker compose -f compose.next.yaml up -d --wait

if [[ "${SEED:-}" == 1 ]]; then
  (cd server && go run ./cmd/seed -reset)
fi

pids=()
run() {
  local name=$1; shift
  ( "$@" 2>&1 | sed -u "s/^/[$name] /" ) &
  pids+=($!)
}
trap 'kill 0' EXIT INT TERM

run fortnox bash -c 'cd server && exec go run ./cmd/fakefortnox'
run server bash -c 'cd server && exec go run .'
run web bash -c 'cd web && exec bun run dev'

until curl -sf localhost:3000/healthz >/dev/null; do sleep 1; done
echo "Ready: http://localhost:5173 (log in as turetek, the kassör; see compose.next.yaml for the others)"
wait
