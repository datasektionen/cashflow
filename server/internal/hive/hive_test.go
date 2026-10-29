package hive

import (
	"context"
	"net/http"
	"net/http/httptest"
	"sync/atomic"
	"testing"
)

func TestPermissionsAreCached(t *testing.T) {
	var requests atomic.Int32
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests.Add(1)
		if r.URL.Path != "/api/v1/user/turetek/permissions" {
			t.Errorf("unexpected path %s", r.URL.Path)
		}
		w.Write([]byte(`[{"id":"pay","scope":null}]`))
	}))
	defer srv.Close()

	c := NewClient(srv.URL, "secret")
	for range 3 {
		p, err := c.Permissions(context.Background(), "turetek")
		if err != nil || !p.Has("pay") {
			t.Fatalf("got %v, %v", p, err)
		}
	}
	if n := requests.Load(); n != 1 {
		t.Errorf("Hive was asked %d times within the TTL, want 1", n)
	}

	c.ttl = 0
	if _, err := c.Permissions(context.Background(), "turetek"); err != nil {
		t.Fatal(err)
	}
	if n := requests.Load(); n != 2 {
		t.Errorf("an expired entry should refetch, got %d requests", n)
	}
}

func TestPermissionsErrorIsNotCached(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "down", http.StatusBadGateway)
	}))
	defer srv.Close()

	c := NewClient(srv.URL, "secret")
	if _, err := c.Permissions(context.Background(), "turetek"); err == nil {
		t.Fatal("want an error when Hive is down")
	}
	if len(c.cache) != 0 {
		t.Error("a failed lookup must not be cached")
	}
}
