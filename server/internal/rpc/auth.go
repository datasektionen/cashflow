// Package rpc implements the Connect services.
package rpc

import (
	"context"
	"errors"
	"log/slog"

	"connectrpc.com/connect"
	auth "github.com/datasektionen/GO-auth-yourself"

	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

type caller struct {
	user  auth.User
	perms perm.Set
}

type callerKey struct{}

// AuthInterceptor rejects anonymous calls and resolves the caller's Hive
// permissions. The session comes from GO-auth-yourself's SessionMiddleware;
// the permissions frozen in the session cookie are ignored in favour of a
// live (cached) Hive lookup.
func AuthInterceptor(h *hive.Client) connect.UnaryInterceptorFunc {
	return func(next connect.UnaryFunc) connect.UnaryFunc {
		return func(ctx context.Context, req connect.AnyRequest) (connect.AnyResponse, error) {
			user, ok := auth.FromContext(ctx)
			if !ok {
				return nil, connect.NewError(connect.CodeUnauthenticated, errors.New("not logged in"))
			}
			perms, err := h.Permissions(ctx, user.Username)
			if err != nil {
				slog.Error("hive lookup failed", "user", user.Username, "error", err)
				return nil, connect.NewError(connect.CodeUnavailable, errors.New("could not reach Hive"))
			}
			ctx = context.WithValue(ctx, callerKey{}, caller{user: user, perms: perm.New(user.Username, perms)})
			return next(ctx, req)
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
