// Package spa serves the web frontend, built by `bun run build:server` in web/
// (or the Dockerfile) into dist/ and embedded in the binary.
package spa

import (
	"embed"
	"io/fs"
	"net/http"
	"path"
	"strings"
)

//go:embed all:dist
var dist embed.FS

const shell = "_shell.html"

// Dist is the embedded frontend build.
func Dist() fs.FS {
	files, _ := fs.Sub(dist, "dist")
	return files
}

// Handler serves built files, and the app shell for every other path so the
// client-side router can take over. Hashed assets are cached forever; the
// shell never is, so a deploy reaches users on their next navigation.
func Handler(files fs.FS) http.Handler {
	fileServer := http.FileServerFS(files)

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		name := strings.TrimPrefix(path.Clean(r.URL.Path), "/")
		if info, err := fs.Stat(files, name); err == nil && !info.IsDir() && name != shell {
			if strings.HasPrefix(name, "assets/") {
				w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
			}
			fileServer.ServeHTTP(w, r)
			return
		}

		page, err := fs.ReadFile(files, shell)
		if err != nil {
			http.Error(w, "Frontend not built: run `bun run build:server` in web/", http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Cache-Control", "no-cache")
		w.Write(page)
	})
}
