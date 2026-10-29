// Package rpc implements the Connect services.
package rpc

import (
	"context"
	"errors"
	"log/slog"

	"connectrpc.com/connect"
	auth "github.com/datasektionen/GO-auth-yourself"

	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

type caller struct {
	user   auth.User
	perms  perm.Set
	viewer claims.Viewer
}

type callerKey struct{}

var (
	ErrNotLoggedIn     = errors.New("not logged in")
	ErrHiveUnavailable = errors.New("could not reach Hive")
)

// ResolveViewer returns the logged-in user's claims.Viewer. The session comes
// from GO-auth-yourself's SessionMiddleware; the permissions frozen in the
// session cookie are ignored in favour of a live (cached) Hive lookup.
func ResolveViewer(ctx context.Context, h *hive.Client) (claims.Viewer, error) {
	c, err := resolve(ctx, h)
	return c.viewer, err
}

func resolve(ctx context.Context, h *hive.Client) (caller, error) {
	user, ok := auth.FromContext(ctx)
	if !ok {
		return caller{}, ErrNotLoggedIn
	}
	hivePerms, err := h.Permissions(ctx, user.Username)
	if err != nil {
		slog.Error("hive lookup failed", "user", user.Username, "error", err)
		return caller{}, ErrHiveUnavailable
	}
	perms := perm.New(user.Username, hivePerms)
	return caller{user: user, perms: perms, viewer: claims.Viewer{Username: user.Username, Perms: perms}}, nil
}

// AuthInterceptor rejects anonymous calls and resolves the caller.
func AuthInterceptor(h *hive.Client) connect.UnaryInterceptorFunc {
	return func(next connect.UnaryFunc) connect.UnaryFunc {
		return func(ctx context.Context, req connect.AnyRequest) (connect.AnyResponse, error) {
			c, err := resolve(ctx, h)
			switch {
			case errors.Is(err, ErrNotLoggedIn):
				return nil, connect.NewError(connect.CodeUnauthenticated, err)
			case err != nil:
				return nil, connect.NewError(connect.CodeUnavailable, err)
			}
			return next(context.WithValue(ctx, callerKey{}, c), req)
		}
	}
}

// callerFrom returns the caller set by AuthInterceptor. Every service is
// mounted behind it, so a missing caller is a wiring bug.
func callerFrom(ctx context.Context) caller {
	c, ok := ctx.Value(callerKey{}).(caller)
	if !ok {
		panic("rpc: handler mounted without AuthInterceptor")
	}
	return c
}
