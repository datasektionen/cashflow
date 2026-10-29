package perm

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/datasektionen/cashflow/server/internal/hive"
)

// permsFrom runs a Hive response through the real client, so these tests also
// cover how scopes are parsed.
func permsFrom(t *testing.T, body string) Set {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer secret" {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		w.Write([]byte(body))
	}))
	t.Cleanup(srv.Close)

	p, err := hive.NewClient(srv.URL, "secret").Permissions(context.Background(), "turetek")
	if err != nil {
		t.Fatal(err)
	}
	return New("turetek", p)
}

func TestScopedAttest(t *testing.T) {
	s := permsFrom(t, `[{"id":"attest","scope":"Ada"},{"id":"attest","scope":"dsys"}]`)
	if !s.MayAttest("ada") || !s.MayAttest("ADA") || !s.MayAttest("DSys") {
		t.Error("scoped attest should match case-insensitively")
	}
	if s.MayAttest("Mottagningen") || s.MayAttestAll() {
		t.Error("attest should be limited to its scopes")
	}
	if !s.MayAttestSome() || !s.IsAdmin() {
		t.Error("any attest scope makes the user an attester and admin")
	}
}

func TestWildcardWinsOverScopes(t *testing.T) {
	for _, body := range []string{
		`[{"id":"accounting","scope":"ada"},{"id":"accounting","scope":"*"}]`,
		`[{"id":"accounting","scope":null},{"id":"accounting","scope":"ada"}]`,
		`[{"id":"accounting","scope":""}]`,
	} {
		s := permsFrom(t, body)
		if !s.MayAccountAll() || !s.MayAccount("anything") {
			t.Errorf("%s: should grant accounting everywhere", body)
		}
	}
}

func TestAccountClaim(t *testing.T) {
	s := permsFrom(t, `[{"id":"accounting","scope":"ada"}]`)
	if !s.MayAccountClaim([]string{"Mottagningen", "Ada"}) {
		t.Error("one matching part should be enough")
	}
	if s.MayAccountClaim([]string{"Mottagningen"}) {
		t.Error("no matching part should deny")
	}
}

func TestViewAll(t *testing.T) {
	if !permsFrom(t, `[{"id":"view-expenses","scope":"*"}]`).MayViewAll() {
		t.Error("view-expenses:* means view all")
	}
	scoped := permsFrom(t, `[{"id":"view-expenses","scope":"ada"}]`)
	if scoped.MayViewAll() || !scoped.MayViewCostCentre("Ada") || scoped.MayViewCostCentre("dsys") {
		t.Error("scoped view-expenses should only see its cost centre")
	}
}

func TestUnscopedOnly(t *testing.T) {
	s := permsFrom(t, `[{"id":"pay","scope":"ada"},{"id":"confirm","scope":null}]`)
	if s.MayPay() {
		t.Error("a scoped pay grant must not allow paying")
	}
	if !s.MayConfirm() {
		t.Error("unscoped confirm should allow confirming")
	}
}
