package web

import (
	"net/url"
	"testing"
)

func TestLegacyPath(t *testing.T) {
	for old, want := range map[string]string{
		// Comment emails.
		"/anna/expenses/12":             "/expenses/12",
		"/anna/invoices/7/update":       "/invoices/7/edit",
		"/admin":                        "/",
		"/admin/attest?cost_centre=Ada": "/attest?cc=Ada",
		"/admin/pay/expenses?user=anna": "/pay?owner=anna",
		"/admin/account/invoices":       "/account",
		"/admin/account/expenses/3":     "/expenses/3/account",
		"/admin/expenses":               "/claims?kind=expense",
		"/admin/invoices/9":             "/invoices/9",
		"/admin/users/anna":             "/users/anna",
		"/admin/vouchers":               "/vouchers",
		"/budget/4":                     "/budget?cc=4",
	} {
		u, _ := url.Parse(old)
		if got, ok := legacyPath(u); !ok || got != want {
			t.Errorf("%s: got %q %v, want %q", old, got, ok, want)
		}
	}
	// Cashflow 4's own pages are left alone.
	for _, path := range []string{"/", "/expenses/12", "/expenses/12/edit", "/invoices/3/account", "/users/anna",
		"/budget", "/claims", "/anna/expenses/0", "/anna/expenses/x", "/admin/unknown"} {
		u, _ := url.Parse(path)
		if got, ok := legacyPath(u); ok {
			t.Errorf("%s should not redirect, got %q", path, got)
		}
	}
}
