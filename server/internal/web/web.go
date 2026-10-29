// Package web wires the HTTP routes: GO-auth-yourself's login routes, the
// Connect services under /api, attachments under /files, health checks, and
// the embedded frontend.
package web

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"connectrpc.com/connect"
	auth "github.com/datasektionen/GO-auth-yourself"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/datasektionen/cashflow/server/gen/cashflow/budget/v1/budgetv1connect"
	"github.com/datasektionen/cashflow/server/gen/cashflow/claim/v1/claimv1connect"
	"github.com/datasektionen/cashflow/server/gen/cashflow/payment/v1/paymentv1connect"
	"github.com/datasektionen/cashflow/server/gen/cashflow/user/v1/userv1connect"
	"github.com/datasektionen/cashflow/server/internal/budget"
	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/rfinger"
	"github.com/datasektionen/cashflow/server/internal/rpc"
	"github.com/datasektionen/cashflow/server/internal/spa"
	"github.com/datasektionen/cashflow/server/internal/storage"
)

// Deps are what the routes need, built once in main.
type Deps struct {
	Pool      *pgxpool.Pool
	PublicURL string
	Budget    *budget.Client
	Pictures  *rfinger.Client
	Hive      *hive.Client
	Files     *storage.Store
}

func NewHandler(ctx context.Context, deps Deps) (http.Handler, error) {
	authCfg := auth.ConfigFromEnv()
	// Same session length as Cashflow 3.
	authCfg.SessionDuration = 48 * time.Hour
	authenticator, err := auth.New(ctx, authCfg)
	if err != nil {
		return nil, fmt.Errorf("init auth: %w", err)
	}

	queries := db.New(deps.Pool)
	claimStore := claims.NewStore(deps.Pool, deps.PublicURL)
	mux := http.NewServeMux()

	// /login, /auth/callback and /logout.
	authenticator.MountAuthRoutes(mux)

	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		if err := deps.Pool.Ping(r.Context()); err != nil {
			http.Error(w, "database unavailable", http.StatusServiceUnavailable)
			return
		}
		w.Write([]byte("ok"))
	})

	api := http.NewServeMux()
	opts := connect.WithInterceptors(rpc.AuthInterceptor(deps.Hive))
	api.Handle(userv1connect.NewUserServiceHandler(&rpc.UserService{Queries: queries, Pictures: deps.Pictures}, opts))
	api.Handle(claimv1connect.NewClaimServiceHandler(&rpc.ClaimService{Store: claimStore}, opts))
	api.Handle(paymentv1connect.NewPaymentServiceHandler(&rpc.PaymentService{Store: claimStore}, opts))
	api.Handle(budgetv1connect.NewBudgetServiceHandler(&rpc.BudgetService{Budget: deps.Budget, Store: claimStore}, opts))
	// The frontend reaches the services at /api/<service>/<method>.
	// Connect uses POST, and GET for side-effect-free calls.
	mux.Handle("POST /api/", http.StripPrefix("/api", api))
	mux.Handle("GET /api/", http.StripPrefix("/api", api))

	mux.Handle("GET /files/{id}", filesHandler(claimStore, deps.Files, deps.Hive))
	mux.Handle("POST /files", uploadHandler(queries, deps.Files, deps.Hive))

	// Everything else is the frontend; more specific routes above win.
	mux.Handle("GET /", spa.Handler(spa.Dist()))

	handler := authenticator.SessionMiddleware(mux)
	return http.NewCrossOriginProtection().Handler(handler), nil
}
