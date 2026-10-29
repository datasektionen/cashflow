package web

import (
	"net/http"
	"net/url"
	"regexp"
	"strings"
)

// Cashflow 3's addresses live on in emails, bookmarks and Fortnox: its
// comment emails link to /<username>/expenses/<id>, and its admin pages sat
// under /admin. legacyPath maps such an address to Cashflow 4's, keeping
// the filters its links carried; ok is false for anything else.
func legacyPath(u *url.URL) (string, bool) {
	segments := strings.Split(strings.Trim(u.Path, "/"), "/")
	q := u.Query()
	search := url.Values{}
	// The admin overview linked to queues with ?cost_centre= and ?user=.
	if cc := q.Get("cost_centre"); cc != "" {
		search.Set("cc", cc)
	}
	if owner := q.Get("user"); owner != "" {
		search.Set("owner", owner)
	}
	with := func(path string) (string, bool) {
		if len(search) == 0 {
			return path, true
		}
		return path + "?" + search.Encode(), true
	}

	switch {
	// /<username>/expenses/<id> and its /update.
	case len(segments) >= 3 && len(segments) <= 4 && isKind(segments[1]) && isID(segments[2]):
		if len(segments) == 3 {
			return with("/" + segments[1] + "/" + segments[2])
		}
		if segments[3] == "update" {
			return with("/" + segments[1] + "/" + segments[2] + "/edit")
		}
	case len(segments) == 2 && segments[0] == "budget" && isID(segments[1]):
		return "/budget?cc=" + segments[1], true
	case segments[0] == "admin":
		return adminPath(segments[1:], search, with)
	}
	return "", false
}

func adminPath(rest []string, search url.Values, with func(string) (string, bool)) (string, bool) {
	page := strings.Join(rest, "/")
	switch page {
	case "":
		return "/", true
	case "attest", "confirm", "payments", "vouchers", "fortnox":
		return with("/" + page)
	case "account", "account/expenses", "account/invoices":
		return with("/account")
	case "pay", "pay/expenses", "pay/invoices":
		return with("/pay")
	case "expenses", "invoices":
		search.Set("kind", strings.TrimSuffix(page, "s"))
		return with("/claims")
	}
	switch {
	case len(rest) == 2 && isKind(rest[0]) && isID(rest[1]):
		return with("/" + rest[0] + "/" + rest[1])
	case len(rest) == 3 && rest[0] == "account" && isKind(rest[1]) && isID(rest[2]):
		return with("/" + rest[1] + "/" + rest[2] + "/account")
	case len(rest) == 2 && rest[0] == "users" && rest[1] != "":
		return "/users/" + url.PathEscape(rest[1]), true
	}
	return "", false
}

func isKind(s string) bool { return s == "expenses" || s == "invoices" }

var idPattern = regexp.MustCompile(`^[1-9][0-9]{0,14}$`)

func isID(s string) bool { return idPattern.MatchString(s) }

// legacyRedirects sends Cashflow 3 addresses on permanently and serves
// everything else from next.
func legacyRedirects(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if target, ok := legacyPath(r.URL); ok {
			http.Redirect(w, r, target, http.StatusMovedPermanently)
			return
		}
		next.ServeHTTP(w, r)
	})
}
