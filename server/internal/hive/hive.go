// Package hive fetches a user's permissions from Hive, Datasektionen's
// permission system, and caches them briefly so revocations apply within a
// minute without a Hive request per API call.
package hive

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// Grant is one permission's scopes. All is true for an unscoped permission or
// the wildcard scope "*"; otherwise Scopes lists the lowercased scopes.
type Grant struct {
	All    bool
	Scopes []string
}

// Permissions maps a permission id to its grant. A missing id means no grant.
type Permissions map[string]Grant

// Has reports whether the user holds perm unscoped (or with the wildcard).
func (p Permissions) Has(perm string) bool {
	return p[perm].All
}

// HasAny reports whether the user holds perm with any scope at all.
func (p Permissions) HasAny(perm string) bool {
	_, ok := p[perm]
	return ok
}

// Grant returns the grant for perm; the zero Grant means none.
func (p Permissions) Grant(perm string) Grant {
	return p[perm]
}

// HasScope reports whether the user holds perm for scope, case-insensitively.
func (p Permissions) HasScope(perm, scope string) bool {
	g, ok := p[perm]
	if !ok {
		return false
	}
	if g.All {
		return true
	}
	scope = strings.ToLower(scope)
	for _, s := range g.Scopes {
		if s == scope {
			return true
		}
	}
	return false
}

type rawPermission struct {
	ID    string  `json:"id"`
	Scope *string `json:"scope"`
}

// parse builds Permissions from Hive's response, matching Cashflow 3: a null,
// empty or "*" scope grants everything and wins over scoped grants.
func parse(raw []rawPermission) Permissions {
	perms := Permissions{}
	for _, r := range raw {
		g := perms[r.ID]
		if r.Scope == nil || *r.Scope == "" || *r.Scope == "*" {
			perms[r.ID] = Grant{All: true}
			continue
		}
		if !g.All {
			g.Scopes = append(g.Scopes, strings.ToLower(*r.Scope))
		}
		perms[r.ID] = g
	}
	return perms
}

type Client struct {
	baseURL string
	secret  string
	http    *http.Client
	ttl     time.Duration

	mu    sync.Mutex
	cache map[string]cached
}

type cached struct {
	perms   Permissions
	fetched time.Time
}

func NewClient(baseURL, secret string) *Client {
	return &Client{
		baseURL: baseURL,
		secret:  secret,
		http:    &http.Client{Timeout: 10 * time.Second},
		ttl:     time.Minute,
		cache:   map[string]cached{},
	}
}

// Permissions returns username's permissions, from the cache when fresh.
func (c *Client) Permissions(ctx context.Context, username string) (Permissions, error) {
	c.mu.Lock()
	entry, ok := c.cache[username]
	c.mu.Unlock()
	if ok && time.Since(entry.fetched) < c.ttl {
		return entry.perms, nil
	}

	perms, err := c.fetch(ctx, username)
	if err != nil {
		return nil, err
	}
	c.mu.Lock()
	c.cache[username] = cached{perms: perms, fetched: time.Now()}
	c.mu.Unlock()
	return perms, nil
}

func (c *Client) fetch(ctx context.Context, username string) (Permissions, error) {
	endpoint := c.baseURL + "/api/v1/user/" + url.PathEscape(username) + "/permissions"
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.secret)

	res, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("hive: %w", err)
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("hive: unexpected status %s", res.Status)
	}
	var raw []rawPermission
	if err := json.NewDecoder(res.Body).Decode(&raw); err != nil {
		return nil, fmt.Errorf("hive: decode permissions: %w", err)
	}
	return parse(raw), nil
}
