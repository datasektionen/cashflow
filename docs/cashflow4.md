# Cashflow 4: developer guide

Cashflow 4 is a Go server (`server/`) with a TanStack Start single-page app (`web/`) embedded in its binary. They
talk over ConnectRPC; the API is defined in `proto/`. Why it is built this way: [rewrite-plan.md](rewrite-plan.md).

## Getting started

You need Go (version in `server/go.mod`), Bun and Docker.

```console
$ cp server/.env.example server/.env
$ (cd web && bun install)
$ make services      # Postgres, mock SSO + Hive (nyckeln), mock rfinger + spam (dock)
$ make dev-server    # terminal 1: http://localhost:3000
$ make dev-web       # terminal 2: http://localhost:5173  <- open this one
```

Log in as any user from `compose.next.yaml` (e.g. `turetek`, the kassör, or `diadat`, who attests one cost centre).
Their Hive permissions are listed there too.

`make check` runs what CI runs. `make fix` formats and applies safe lint fixes. `make gen` regenerates code after
editing `proto/` or SQL queries; generated code is committed and CI fails if it is stale.

## Layout

```
proto/cashflow/<service>/v1/      API: services, messages, error details
server/
  main.go                         startup: config, database, HTTP server
  internal/config                 environment variables
  internal/database               pool + migrations (migrations/*.sql), queries/*.sql → db/ (sqlc)
  internal/hive, internal/perm    Hive client; Cashflow's permission rules (port of cashflow/dauth.py)
  internal/rpc                    Connect service implementations
  internal/spa                    serves the embedded frontend build
  internal/web                    route wiring
web/src/
  routes/                         file-based routes; _app/ is everything behind login
  components/ui/                  shadcn components (vendored; add with `bun run ui:add <name>`)
  components/form/                the form kit (useAppForm and field components)
  components/layout/              app frame, page frame, empty/error states
  lib/                            i18n, navigation, money and bank formatting, RPC transport
  gen/                            generated API client
```

## Conventions

**Money** is an integer number of öre everywhere: `bigint` in Postgres, `int64` in proto, `bigint` in TypeScript. Only
`formatOre` in `web/src/lib/money.ts` turns it into a decimal, for display.

**Permissions** are checked on the server for every action; the `Capabilities` in `GetMe` only decide what the
frontend shows. Permission rules live in `server/internal/perm` and nowhere else.

**Validation** happens on the server. A handler collects problems with `violations.add(field, code)` and returns
`v.err()`, an `InvalidArgument` error carrying `FieldViolations`. The frontend shows each code's message from
`t.validation` next to its field (`applyServerErrors`). Codes are `<field>.<rule>`, e.g. `bank_account.length`.

**Text** never appears inline in components. Swedish (`web/src/lib/i18n/sv.ts`) defines the keys; English must
match, or the build fails. Use `const t = useT()`.

## Recipes

### Add an RPC

1. Add the method and messages to `proto/cashflow/<service>/v1/*.proto` (`option idempotency_level =
   NO_SIDE_EFFECTS` for reads, so they use GET and can be cached).
2. If it needs SQL, add a named query to `server/internal/database/queries/*.sql`.
3. `make gen`, then implement the method in `server/internal/rpc`. New services are mounted in
   `internal/web/web.go` behind `rpc.AuthInterceptor`.
4. Call it from the web app with the generated connect-query hooks: `useSuspenseQuery(method, input)` or
   `useMutation(method)`. Prefetch in the route's `loader` with
   `context.queryClient.ensureQueryData(createQueryOptions(method, input, { transport }))`.

### Add a page

1. Create `web/src/routes/_app/<path>.tsx`; the route tree regenerates when Vite runs.
2. Wrap the content in `<Page title=…>`.
3. If it belongs in the sidebar, add it to `web/src/lib/navigation.ts` with an icon, a `G <key>` shortcut and who may
   see it. The sidebar, the shortcut and the shortcuts dialog all pick it up from there.

### Add a form

Use `useAppForm` with `form.AppField` and the field components, as in `routes/_app/profile.tsx`. In `onSubmit`,
call the mutation and pass errors to `applyServerErrors(formApi, error, t)`. New field types go in
`components/form/` and are registered in `form.ts`, so every form gets them with the same labels and errors.

### Change the schema

Add a new numbered pair `server/internal/database/migrations/00000N_<name>.{up,down}.sql`. Never edit a migration
that has been deployed. The server applies migrations on startup.
