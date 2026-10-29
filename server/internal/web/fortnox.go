package web

import (
	"crypto/rand"
	"crypto/subtle"
	"encoding/base64"
	"errors"
	"log/slog"
	"net/http"
	"strings"

	"github.com/datasektionen/cashflow/server/internal/fortnox"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/rpc"
)

// The treasurer connects Fortnox by approving Cashflow there: /fortnox/auth
// sends the browser to Fortnox, which sends it back to /fortnox/auth/complete
// with a code. A random state in a short-lived cookie ties the two together,
// as Cashflow 3 does with its session. Either way the browser ends up on the
// Fortnox page with ?result=… for it to explain.
const (
	fortnoxStateCookie = "fortnox_state"
	fortnoxPage        = "/fortnox"
)

type fortnoxAuth struct {
	fortnox   *fortnox.Client
	hive      *hive.Client
	publicURL string
}

func (a fortnoxAuth) redirectURI() string {
	return strings.TrimSuffix(a.publicURL, "/") + "/fortnox/auth/complete"
}

func (a fortnoxAuth) done(w http.ResponseWriter, r *http.Request, result string) {
	http.Redirect(w, r, fortnoxPage+"?result="+result, http.StatusFound)
}

// allowed: only those who manage Fortnox (unscoped) may connect it.
func (a fortnoxAuth) allowed(w http.ResponseWriter, r *http.Request) (string, bool) {
	viewer, err := rpc.ResolveViewer(r.Context(), a.hive)
	switch {
	case errors.Is(err, rpc.ErrNotLoggedIn):
		http.Redirect(w, r, "/login", http.StatusFound)
		return "", false
	case err != nil:
		http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
		return "", false
	case !a.fortnox.Enabled():
		a.done(w, r, "disabled")
		return "", false
	case !viewer.Perms.MayManageFortnox():
		a.done(w, r, "forbidden")
		return "", false
	}
	return viewer.Username, true
}

func (a fortnoxAuth) start(w http.ResponseWriter, r *http.Request) {
	if _, ok := a.allowed(w, r); !ok {
		return
	}
	b := make([]byte, 32)
	rand.Read(b)
	state := base64.RawURLEncoding.EncodeToString(b)
	http.SetCookie(w, &http.Cookie{
		Name: fortnoxStateCookie, Value: state, Path: "/fortnox/auth", MaxAge: 600,
		HttpOnly: true, Secure: strings.HasPrefix(a.publicURL, "https://"), SameSite: http.SameSiteLaxMode,
	})
	http.Redirect(w, r, a.fortnox.AuthCodeURL(a.redirectURI(), state), http.StatusFound)
}

func (a fortnoxAuth) complete(w http.ResponseWriter, r *http.Request) {
	username, ok := a.allowed(w, r)
	if !ok {
		return
	}
	cookie, err := r.Cookie(fortnoxStateCookie)
	http.SetCookie(w, &http.Cookie{Name: fortnoxStateCookie, Path: "/fortnox/auth", MaxAge: -1})
	q := r.URL.Query()
	if err != nil || subtle.ConstantTimeCompare([]byte(cookie.Value), []byte(q.Get("state"))) != 1 {
		slog.Warn("fortnox auth: state mismatch", "user", username)
		a.done(w, r, "error")
		return
	}
	if q.Get("code") == "" {
		// The treasurer declined, or Fortnox failed.
		slog.Warn("fortnox auth: no code", "user", username, "error", q.Get("error"))
		a.done(w, r, "cancelled")
		return
	}
	if err := a.fortnox.Connect(r.Context(), username, q.Get("code"), a.redirectURI()); err != nil {
		slog.Error("fortnox auth: token exchange failed", "user", username, "error", err)
		a.done(w, r, "error")
		return
	}
	a.done(w, r, "connected")
}
