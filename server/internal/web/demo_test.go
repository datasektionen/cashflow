package web

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestDemoRoutes(t *testing.T) {
	t.Setenv("DEMO_MODE", "true")
	t.Setenv("APP_SECRET_KEY", strings.Repeat("k", 32))
	mocks := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/oauth-v1/token" || r.Method != "POST" {
			t.Errorf("unexpected proxy request: %s %s", r.Method, r.URL.Path)
		}
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"access_token":"fake"}`))
	}))
	defer mocks.Close()
	t.Setenv("FORTNOX_API_URL", mocks.URL+"/3")
	handler, err := NewHandler(context.Background(), Deps{PublicURL: "https://demo.invalid"})
	if err != nil {
		t.Fatal(err)
	}
	for _, path := range []string{"/login", "/demo/status"} {
		w := httptest.NewRecorder()
		handler.ServeHTTP(w, httptest.NewRequest("GET", "https://demo.invalid"+path, nil))
		if w.Code != 200 {
			t.Fatalf("%s: %d %s", path, w.Code, w.Body.String())
		}
	}
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, httptest.NewRequest("POST", "https://demo.invalid/demo/fortnox/oauth-v1/token", strings.NewReader("grant_type=authorization_code")))
	if w.Code != 200 || !strings.Contains(w.Body.String(), "access_token") {
		t.Fatalf("mock token exchange: %d %s", w.Code, w.Body.String())
	}
}
