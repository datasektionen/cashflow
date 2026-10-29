package web

import (
	"errors"
	"io"
	"log/slog"
	"mime"
	"net/http"
	"path"
	"strconv"

	"github.com/jackc/pgx/v5"

	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/rpc"
	"github.com/datasektionen/cashflow/server/internal/storage"
)

// Types a browser may render in place. Anything else, including SVG and HTML
// that could run script on our origin, is downloaded instead.
var inlineTypes = map[string]bool{
	"image/jpeg":      true,
	"image/png":       true,
	"image/webp":      true,
	"image/gif":       true,
	"application/pdf": true,
}

// filesHandler streams a claim attachment to anyone who may view the claim.
// Unlike Cashflow 3's presigned S3 links, every request is checked, and links
// are same-origin so PDFs embed without CORS.
func filesHandler(store *claims.Store, files *storage.Store, h *hive.Client) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ctx := r.Context()
		viewer, err := rpc.ResolveViewer(ctx, h)
		switch {
		case errors.Is(err, rpc.ErrNotLoggedIn):
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		case err != nil:
			http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
			return
		}

		// Unknown and invisible files look the same, so ids cannot be probed.
		id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
		if err != nil {
			http.NotFound(w, r)
			return
		}
		file, err := store.Queries.GetFile(ctx, id)
		if errors.Is(err, pgx.ErrNoRows) {
			http.NotFound(w, r)
			return
		} else if err != nil {
			serverError(w, "get file", err)
			return
		}
		if visible, err := store.Visible(ctx, viewer, file.ClaimID); err != nil {
			serverError(w, "check file visibility", err)
			return
		} else if !visible {
			http.NotFound(w, r)
			return
		}

		obj, err := files.Open(ctx, file.File)
		if errors.Is(err, storage.ErrNotFound) {
			slog.Warn("file missing from storage", "file_id", id, "name", file.File)
			http.NotFound(w, r)
			return
		} else if err != nil {
			serverError(w, "open file", err)
			return
		}
		defer obj.Body.Close()

		disposition := "attachment"
		if inlineTypes[obj.ContentType] {
			disposition = "inline"
		}
		header := w.Header()
		header.Set("Content-Type", obj.ContentType)
		header.Set("Content-Disposition", mime.FormatMediaType(disposition, map[string]string{"filename": path.Base(file.File)}))
		header.Set("X-Content-Type-Options", "nosniff")
		// Attachments never change; the session decides who sees them.
		header.Set("Cache-Control", "private, max-age=86400, immutable")
		if obj.ContentLength > 0 {
			header.Set("Content-Length", strconv.FormatInt(obj.ContentLength, 10))
		}
		if _, err := io.Copy(w, obj.Body); err != nil {
			slog.Warn("file stream interrupted", "file_id", id, "error", err)
		}
	})
}

func serverError(w http.ResponseWriter, what string, err error) {
	slog.Error(what, "error", err)
	http.Error(w, "Internal Server Error", http.StatusInternalServerError)
}
