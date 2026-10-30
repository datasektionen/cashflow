// Package web wires the HTTP routes: GO-auth-yourself's login routes, the
// Connect services under /api, attachments under /files, connecting Fortnox
// under /fortnox/auth, health checks, and
// the embedded frontend.
package web

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"time"

	"connectrpc.com/connect"
	auth "github.com/datasektionen/GO-auth-yourself"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/datasektionen/cashflow/server/gen/cashflow/accounting/v1/accountingv1connect"
	"github.com/datasektionen/cashflow/server/gen/cashflow/budget/v1/budgetv1connect"
	"github.com/datasektionen/cashflow/server/gen/cashflow/claim/v1/claimv1connect"
	"github.com/datasektionen/cashflow/server/gen/cashflow/payment/v1/paymentv1connect"
	"github.com/datasektionen/cashflow/server/gen/cashflow/stats/v1/statsv1connect"
	"github.com/datasektionen/cashflow/server/gen/cashflow/user/v1/userv1connect"
	"github.com/datasektionen/cashflow/server/internal/budget"
	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/demo"
	"github.com/datasektionen/cashflow/server/internal/fortnox"
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
	Fortnox   *fortnox.Client // nil when Fortnox is off
}

func NewHandler(ctx context.Context, deps Deps) (http.Handler, error) {
	authCfg := auth.ConfigFromEnv()
	// Same session length as Cashflow 3.
	authCfg.SessionDuration = 48 * time.Hour
	var mountAuth func(*http.ServeMux)
	var sessionMiddleware func(http.Handler) http.Handler
	if demo.Enabled() {
		authenticator, err := demo.New(authCfg.SecretKey, deps.PublicURL)
		if err != nil {
			return nil, err
		}
		mountAuth, sessionMiddleware = authenticator.Mount, authenticator.Middleware
	} else {
		authenticator, err := auth.New(ctx, authCfg)
		if err != nil {
			return nil, fmt.Errorf("init auth: %w", err)
		}
		mountAuth, sessionMiddleware = authenticator.MountAuthRoutes, authenticator.SessionMiddleware
	}

	queries := db.New(deps.Pool)
	claimStore := claims.NewStore(deps.Pool, deps.PublicURL)
	mux := http.NewServeMux()

	// /login, /auth/callback and /logout.
	mountAuth(mux)
	mux.HandleFunc("GET /demo/status", demo.Status)
	if demo.Enabled() {
		target, err := url.Parse(os.Getenv("FORTNOX_API_URL"))
		if err != nil || target.Host == "" {
			return nil, fmt.Errorf("demo requires a mock Fortnox URL")
		}
		target.Path = ""
		proxy := httputil.NewSingleHostReverseProxy(target)
		mux.Handle("GET /demo/fortnox/oauth-v1/auth", http.StripPrefix("/demo/fortnox", proxy))
	}

	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		if err := deps.Pool.Ping(r.Context()); err != nil {
			http.Error(w, "database unavailable", http.StatusServiceUnavailable)
			return
		}
		w.Write([]byte("ok"))
	})

	api := http.NewServeMux()
	opts := connect.WithInterceptors(rpc.AuthInterceptor(deps.Hive))
	claimService := &rpc.ClaimService{Store: claimStore}
	api.Handle(userv1connect.NewUserServiceHandler(&rpc.UserService{Queries: queries, Pictures: deps.Pictures, Fortnox: deps.Fortnox}, opts))
	api.Handle(claimv1connect.NewClaimServiceHandler(claimService, opts))
	api.Handle(paymentv1connect.NewPaymentServiceHandler(&rpc.PaymentService{Store: claimStore}, opts))
	api.Handle(budgetv1connect.NewBudgetServiceHandler(&rpc.BudgetService{Budget: deps.Budget, Store: claimStore}, opts))
	api.Handle(statsv1connect.NewStatsServiceHandler(&rpc.StatsService{Queries: queries}, opts))
	api.Handle(accountingv1connect.NewAccountingServiceHandler(&rpc.AccountingService{
		Store: claimStore, Claims: claimService, Fortnox: deps.Fortnox, Budget: deps.Budget,
	}, opts))
	// The frontend reaches the services at /api/<service>/<method>.
	// Connect uses POST, and GET for side-effect-free calls.
	mux.Handle("POST /api/", http.StripPrefix("/api", api))
	mux.Handle("GET /api/", http.StripPrefix("/api", api))

	mux.Handle("GET /files/{id}", filesHandler(claimStore, deps.Files, deps.Hive))
	mux.Handle("POST /files", uploadHandler(queries, deps.Files, deps.Hive))

	fortnoxAuth := fortnoxAuth{fortnox: deps.Fortnox, hive: deps.Hive, publicURL: deps.PublicURL}
	mux.HandleFunc("GET /fortnox/auth", fortnoxAuth.start)
	mux.HandleFunc("GET /fortnox/auth/complete", fortnoxAuth.complete)

	// Everything else is the frontend; more specific routes above win.
	// Cashflow 3's addresses redirect to their new places.
	mux.Handle("GET /", legacyRedirects(spa.Handler(spa.Dist())))

	handler := sessionMiddleware(mux)
	return securityHeaders(http.NewCrossOriginProtection().Handler(handler)), nil
}
