package demo

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"

	auth "github.com/datasektionen/GO-auth-yourself"
	"github.com/golang-jwt/jwt/v5"
)

func TestDemoSessions(t *testing.T) {
	a, err := New(strings.Repeat("k", 32), "https://demo.invalid")
	if err != nil {
		t.Fatal(err)
	}
	mux := http.NewServeMux()
	a.Mount(mux)
	mux.HandleFunc("GET /me", func(w http.ResponseWriter, r *http.Request) {
		u, ok := auth.FromContext(r.Context())
		if !ok {
			w.WriteHeader(401)
			return
		}
		w.Write([]byte(u.Username))
	})
	handler := http.NewCrossOriginProtection().Handler(a.Middleware(mux))
	for _, p := range Personas {
		t.Run(p.Username, func(t *testing.T) {
			req := httptest.NewRequest("POST", "https://demo.invalid/demo/login", strings.NewReader(url.Values{"user": {p.Username}}.Encode()))
			req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
			w := httptest.NewRecorder()
			handler.ServeHTTP(w, req)
			if w.Code != 303 || w.Header().Get("Location") != "/" {
				t.Fatalf("login: %d %s", w.Code, w.Body.String())
			}
			cookies := w.Result().Cookies()
			if len(cookies) != 1 || !cookies[0].HttpOnly || !cookies[0].Secure {
				t.Fatal("unsafe cookie")
			}
			req = httptest.NewRequest("GET", "https://demo.invalid/me", nil)
			req.AddCookie(cookies[0])
			w = httptest.NewRecorder()
			handler.ServeHTTP(w, req)
			if w.Code != 200 || w.Body.String() != p.Username {
				t.Fatalf("session: %d %s", w.Code, w.Body.String())
			}
		})
	}
	expired, _ := jwt.NewWithClaims(jwt.SigningMethodHS256, session{jwt.RegisteredClaims{Subject: "turetek", Issuer: "cashflow-demo", ExpiresAt: jwt.NewNumericDate(time.Now().Add(-time.Hour))}}).SignedString(a.key)
	for _, token := range []string{"invalid", expired} {
		req := httptest.NewRequest("GET", "https://demo.invalid/me", nil)
		req.AddCookie(&http.Cookie{Name: "cashflow_demo", Value: token})
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, req)
		if w.Code != 401 {
			t.Fatal("invalid session accepted")
		}
	}
	req := httptest.NewRequest("POST", "https://demo.invalid/demo/login", strings.NewReader("user=someone"))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)
	if w.Code != 400 {
		t.Fatal("unknown user accepted")
	}
	req = httptest.NewRequest("POST", "https://demo.invalid/demo/login", strings.NewReader("user=turetek"))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	req.Header.Set("Origin", "https://evil.invalid")
	w = httptest.NewRecorder()
	handler.ServeHTTP(w, req)
	if w.Code != 403 {
		t.Fatal("cross-origin login accepted")
	}
	req = httptest.NewRequest("GET", "https://demo.invalid/logout", nil)
	w = httptest.NewRecorder()
	handler.ServeHTTP(w, req)
	if c := w.Result().Cookies(); len(c) != 1 || c[0].MaxAge != -1 {
		t.Fatal("logout did not clear cookie")
	}
}
