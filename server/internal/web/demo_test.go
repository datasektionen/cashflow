package web

import (
	"context"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestDemoRoutes(t *testing.T) {
	t.Setenv("DEMO_MODE", "true")
	t.Setenv("APP_SECRET_KEY", strings.Repeat("k", 32))
	t.Setenv("FORTNOX_API_URL", "http://mocks:9004/3")
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
}
