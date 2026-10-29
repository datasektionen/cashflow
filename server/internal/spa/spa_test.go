package spa

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"testing/fstest"
)

func TestHandler(t *testing.T) {
	files := fstest.MapFS{
		"_shell.html":         {Data: []byte("<html>shell</html>")},
		"favicon.svg":         {Data: []byte("<svg/>")},
		"assets/index-abc.js": {Data: []byte("js")},
	}
	h := Handler(files)

	tests := []struct {
		path, body, cache string
	}{
		{"/", "<html>shell</html>", "no-cache"},
		{"/attest", "<html>shell</html>", "no-cache"},
		{"/expenses/new", "<html>shell</html>", "no-cache"},
		{"/assets/index-abc.js", "js", "public, max-age=31536000, immutable"},
		{"/favicon.svg", "<svg/>", ""},
		// The shell is only reachable through the fallback, with its headers.
		{"/_shell.html", "<html>shell</html>", "no-cache"},
	}
	for _, tt := range tests {
		rec := httptest.NewRecorder()
		h.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, tt.path, nil))
		if rec.Code != http.StatusOK || rec.Body.String() != tt.body {
			t.Errorf("%s: got %d %q", tt.path, rec.Code, rec.Body.String())
		}
		if got := rec.Header().Get("Cache-Control"); got != tt.cache {
			t.Errorf("%s: Cache-Control %q, want %q", tt.path, got, tt.cache)
		}
	}
}

func TestHandlerWithoutBuild(t *testing.T) {
	rec := httptest.NewRecorder()
	Handler(fstest.MapFS{}).ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/", nil))
	if rec.Code != http.StatusNotFound {
		t.Errorf("got %d, want 404 with a hint to build the frontend", rec.Code)
	}
}
