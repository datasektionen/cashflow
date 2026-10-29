// Package web wires the HTTP routes: GO-auth-yourself's login routes, the
// Connect services under /api, health checks, and the embedded frontend.
package web

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"connectrpc.com/connect"
	auth "github.com/datasektionen/GO-auth-yourself"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/datasektionen/cashflow/server/gen/cashflow/user/v1/userv1connect"
	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/rpc"
	"github.com/datasektionen/cashflow/server/internal/spa"
)

func NewHandler(ctx context.Context, pool *pgxpool.Pool, hiveClient *hive.Client) (http.Handler, error) {
	authCfg := auth.ConfigFromEnv()
	// Same session length as Cashflow 3.
	authCfg.SessionDuration = 48 * time.Hour
	authenticator, err := auth.New(ctx, authCfg)
	if err != nil {
		return nil, fmt.Errorf("init auth: %w", err)
	}

	queries := db.New(pool)
	mux := http.NewServeMux()

	// /login, /auth/callback and /logout.
	authenticator.MountAuthRoutes(mux)

	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, r *http.Request) {
		if err := pool.Ping(r.Context()); err != nil {
			http.Error(w, "database unavailable", http.StatusServiceUnavailable)
			return
		}
		w.Write([]byte("ok"))
	})

	api := http.NewServeMux()
	opts := connect.WithInterceptors(rpc.AuthInterceptor(hiveClient))
	api.Handle(userv1connect.NewUserServiceHandler(&rpc.UserService{Queries: queries}, opts))
	// The frontend reaches the services at /api/<service>/<method>.
	// Connect uses POST, and GET for side-effect-free calls.
	mux.Handle("POST /api/", http.StripPrefix("/api", api))
	mux.Handle("GET /api/", http.StripPrefix("/api", api))

	// Everything else is the frontend; more specific routes above win.
	mux.Handle("GET /", spa.Handler())

	handler := authenticator.SessionMiddleware(mux)
	return http.NewCrossOriginProtection().Handler(handler), nil
}
