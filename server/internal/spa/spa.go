// Package spa serves the web frontend, built by `bun run build:server` in web/
// (or the Dockerfile) into dist/ and embedded in the binary.
package spa

import (
	"crypto/sha256"
	"embed"
	"encoding/base64"
	"io/fs"
	"net/http"
	"path"
	"regexp"
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
	page, pageErr := fs.ReadFile(files, shell)
	csp := ContentSecurityPolicy(page)

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		name := strings.TrimPrefix(path.Clean(r.URL.Path), "/")
		if info, err := fs.Stat(files, name); err == nil && !info.IsDir() && name != shell {
			if strings.HasPrefix(name, "assets/") {
				w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
			}
			fileServer.ServeHTTP(w, r)
			return
		}

		if pageErr != nil {
			http.Error(w, "Frontend not built: run `bun run build:server` in web/", http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Security-Policy", csp)
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Cache-Control", "no-cache")
		w.Write(page)
	})
}

var inlineScript = regexp.MustCompile(`(?s)<script(\s[^>]*)?>(.*?)</script>`)

// ContentSecurityPolicy allows the shell's own inline scripts (the theme
// and router bootstrap the build writes) by hash, and nothing inline
// besides; scripts otherwise only come from the app's own origin.
//   - 'wasm-unsafe-eval' and blob: workers: converting iPhone photos (heic-to)
//     runs WebAssembly in a worker made from a blob.
//   - images from https: profile pictures come from rfinger's storage.
//   - inline styles: components set CSS variables, e.g. a cost centre's hue.
//   - frames: the receipt viewer shows PDFs from /files and blob: previews.
func ContentSecurityPolicy(page []byte) string {
	scripts := []string{"'self'", "'wasm-unsafe-eval'"}
	for _, m := range inlineScript.FindAllSubmatch(page, -1) {
		if strings.Contains(string(m[1]), "src=") {
			continue
		}
		sum := sha256.Sum256(m[2])
		scripts = append(scripts, "'sha256-"+base64.StdEncoding.EncodeToString(sum[:])+"'")
	}
	return strings.Join([]string{
		"default-src 'self'",
		"script-src " + strings.Join(scripts, " "),
		"style-src 'self' 'unsafe-inline'",
		"img-src 'self' data: blob: https:",
		"font-src 'self' data:",
		"connect-src 'self'",
		"worker-src 'self' blob:",
		"frame-src 'self' blob:",
		"frame-ancestors 'none'",
		"object-src 'none'",
		"base-uri 'self'",
		"form-action 'self'",
	}, "; ")
}
