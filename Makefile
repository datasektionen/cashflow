# Cashflow 4 (server/, web/, proto/). Cashflow 3 still runs from compose.yaml.

.PHONY: services dev-server dev-web gen check fix build django-schema

## Postgres, mock SSO/Hive (nyckeln) and mock rfinger/spam (dock).
services:
	docker compose -f compose.next.yaml up -d

## The Go server on :3000. Reads server/.env (copy server/.env.example).
dev-server:
	cd server && go run .

## The web app on :5173, forwarding API and login routes to the server.
dev-web:
	cd web && bun run dev

## Regenerate code from proto/ (Go + TypeScript) and server/internal/database/queries (sqlc).
gen:
	cd proto && ../web/node_modules/.bin/buf lint && ../web/node_modules/.bin/buf generate
	cd server && go tool sqlc generate

## Everything CI runs, except the image build.
check:
	cd proto && ../web/node_modules/.bin/buf lint
	cd server && test -z "$$(gofmt -l .)" && go vet ./... && go tool staticcheck ./... && TEST_DATABASE_URL=postgres://cashflow:cashflow@localhost:5433/cashflow go test ./...
	cd web && bunx biome ci . && bunx tsc --noEmit && bunx vitest run

## Format and apply safe lint fixes.
fix:
	cd server && gofmt -w .
	cd web && bunx biome check --write .

## The production image, as deployed.
build:
	docker build -f Dockerfile.next -t cashflow-next .

## Refresh server/internal/database/cashflow3/schema.sql after a Django migration:
## runs Cashflow 3's migrations in a scratch database and dumps the result.
django-schema:
	./scripts/django-schema.sh
