// Package demo provides explicitly enabled, isolated demonstration identities.
// Production continues to use OIDC. Never enable DEMO_MODE with real data.
package demo

import (
	"embed"
	"encoding/json"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"strings"
	"time"

	auth "github.com/datasektionen/GO-auth-yourself"
	"github.com/golang-jwt/jwt/v5"
)

type Persona struct {
	Username    string
	Name        string
	Role        string
	Description string
	Permissions []auth.Permission
}

var Personas = []Persona{
	{"turetek", "Ture Teknolog", "Kassör · Treasurer", "Alla kostnadsställen: attestera, bekräfta, bokföra, betala och hantera Fortnox.", grants("accounting", "attest", "confirm", "delete", "edit-invoice", "moderate-comments", "pay", "unattest", "unconfirm", "view-all-payments", "attest-firmatecknare", "manage-fortnox", "view-expenses")},
	{"diadat", "Diana Datalog", "Attestant · Approver", "Attesterar Sektionslokalsgruppen och kan bokföra alla kostnadsställen.", []auth.Permission{{ID: "attest", Scope: "Sektionslokalsgruppen"}, {ID: "accounting", Scope: "*"}}},
	{"bilbek", "Bilbo Baggins", "Bokförare · Scoped accountant", "Kan bokföra Mottagningen 2026, men inte attestera eller betala.", []auth.Permission{{ID: "accounting", Scope: "Mottagningen 2026"}}},
	{"sauron", "Sauron Mordor", "Granskare · Viewer", "Ser alla ärenden utan behörighet att attestera, bokföra eller betala.", []auth.Permission{{ID: "view-all"}}},
	{"marmed", "Martin Median", "Medlem · Member", "Skapar egna utlägg och fakturor och följer sina ärenden. Inga administratörsrättigheter.", []auth.Permission{}},
	{"jobjav", "Jobbig Speciell", "Ny medlem · New member", "Som en vanlig medlem, med saknade bankuppgifter för att testa introduktionen.", []auth.Permission{}},
}

func grants(ids ...string) []auth.Permission {
	out := make([]auth.Permission, 0, len(ids))
	for _, id := range ids {
		out = append(out, auth.Permission{ID: id, Scope: "*"})
	}
	return out
}
func Enabled() bool { return os.Getenv("DEMO_MODE") == "true" }
func Find(username string) (Persona, bool) {
	for _, p := range Personas {
		if p.Username == username {
			return p, true
		}
	}
	return Persona{}, false
}

//go:embed login.html
var templates embed.FS
var loginPage = template.Must(template.ParseFS(templates, "login.html"))

type session struct {
	jwt.RegisteredClaims
}
type Auth struct {
	key    []byte
	secure bool
}

func New(secret, publicURL string) (*Auth, error) {
	if len(secret) < 32 {
		return nil, fmt.Errorf("demo session key must be at least 32 bytes")
	}
	return &Auth{key: []byte(secret), secure: strings.HasPrefix(publicURL, "https://")}, nil
}
func (a *Auth) Mount(mux *http.ServeMux) {
	mux.HandleFunc("GET /login", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		_ = loginPage.Execute(w, Personas)
	})
	mux.HandleFunc("POST /demo/login", func(w http.ResponseWriter, r *http.Request) {
		if err := r.ParseForm(); err != nil {
			http.Error(w, "invalid form", 400)
			return
		}
		p, ok := Find(r.PostForm.Get("user"))
		if !ok {
			http.Error(w, "unknown demo user", 400)
			return
		}
		now := time.Now()
		token, err := jwt.NewWithClaims(jwt.SigningMethodHS256, session{jwt.RegisteredClaims{
			Subject: p.Username, Issuer: "cashflow-demo", IssuedAt: jwt.NewNumericDate(now), ExpiresAt: jwt.NewNumericDate(now.Add(48 * time.Hour)),
		}}).SignedString(a.key)
		if err != nil {
			http.Error(w, "could not create session", 500)
			return
		}
		http.SetCookie(w, a.cookie(token, 172800))
		http.Redirect(w, r, "/", http.StatusSeeOther)
	})
	mux.HandleFunc("GET /logout", func(w http.ResponseWriter, r *http.Request) {
		http.SetCookie(w, a.cookie("", -1))
		http.Redirect(w, r, "/login", http.StatusSeeOther)
	})
}
func (a *Auth) cookie(value string, age int) *http.Cookie {
	return &http.Cookie{Name: "cashflow_demo", Value: value, Path: "/", HttpOnly: true, Secure: a.secure, SameSite: http.SameSiteLaxMode, MaxAge: age}
}
func (a *Auth) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("X-Robots-Tag", "noindex, nofollow")
		if cookie, err := r.Cookie("cashflow_demo"); err == nil {
			var claims session
			_, err := jwt.ParseWithClaims(cookie.Value, &claims, func(*jwt.Token) (any, error) { return a.key, nil }, jwt.WithValidMethods([]string{"HS256"}), jwt.WithExpirationRequired(), jwt.WithIssuer("cashflow-demo"))
			if err == nil {
				if p, ok := Find(claims.Subject); ok {
					r = r.WithContext(auth.ContextWithUser(r.Context(), auth.User{Username: p.Username, Name: p.Name, Email: p.Username + "@demo.invalid"}))
				}
			}
		}
		next.ServeHTTP(w, r)
	})
}
func Status(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	_ = json.NewEncoder(w).Encode(map[string]bool{"enabled": Enabled()})
}
