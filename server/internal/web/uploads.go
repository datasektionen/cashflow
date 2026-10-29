package web

import (
	"bytes"
	"crypto/rand"
	"encoding/base32"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"path"
	"strings"
	"unicode"

	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/rpc"
	"github.com/datasektionen/cashflow/server/internal/storage"
)

// Uploads larger than this are refused; phone photos are a few MB.
const maxUploadBytes = 25 << 20

// Accepted types by their content, with the extension stored files get.
// HEIC photos are converted to JPEG in the browser before upload.
var uploadTypes = map[string]string{
	"image/jpeg":      ".jpg",
	"image/png":       ".png",
	"image/webp":      ".webp",
	"application/pdf": ".pdf",
}

type uploadResponse struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	ContentType string `json:"contentType"`
	Size        int64  `json:"size"`
}

// uploadHandler stores one file ahead of a claim form being submitted and
// answers with an id the form sends along (POST /files, field "file").
func uploadHandler(queries *db.Queries, files *storage.Store, h *hive.Client) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		viewer, err := rpc.ResolveViewer(r.Context(), h)
		switch {
		case errors.Is(err, rpc.ErrNotLoggedIn):
			http.Error(w, "Unauthorized", http.StatusUnauthorized)
			return
		case err != nil:
			http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
			return
		}

		r.Body = http.MaxBytesReader(w, r.Body, maxUploadBytes+1<<20)
		file, header, err := r.FormFile("file")
		if err != nil {
			uploadError(w, http.StatusBadRequest, "upload.missing")
			return
		}
		defer file.Close()
		body, err := io.ReadAll(io.LimitReader(file, maxUploadBytes+1))
		if err != nil {
			uploadError(w, http.StatusBadRequest, "upload.unreadable")
			return
		}
		if len(body) > maxUploadBytes {
			uploadError(w, http.StatusRequestEntityTooLarge, "upload.too_large")
			return
		}
		contentType := http.DetectContentType(body)
		ext, ok := uploadTypes[contentType]
		if !ok {
			uploadError(w, http.StatusUnsupportedMediaType, "upload.type")
			return
		}

		id := newUploadID()
		name := safeName(header.Filename, ext)
		// core_file.file is varchar(100); "c4/<26-char id>/" leaves room for the name.
		key := "c4/" + id + "/" + name
		if err := files.Put(r.Context(), key, bytes.NewReader(body)); err != nil {
			serverError(w, "store upload", err)
			return
		}
		if err := queries.InsertUpload(r.Context(), db.InsertUploadParams{
			ID: id, Uploader: viewer.Username, StorageKey: key, Filename: name, ContentType: contentType, SizeBytes: int64(len(body)),
		}); err != nil {
			serverError(w, "record upload", err)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(uploadResponse{ID: id, Name: name, ContentType: contentType, Size: int64(len(body))})
	})
}

func uploadError(w http.ResponseWriter, status int, code string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]string{"code": code})
}

func newUploadID() string {
	b := make([]byte, 16)
	rand.Read(b)
	return strings.ToLower(base32.StdEncoding.WithPadding(base32.NoPadding).EncodeToString(b))
}

// safeName keeps a readable file name with only letters, digits, dots,
// dashes and underscores, at most 60 characters, ending in ext.
func safeName(original, ext string) string {
	base := strings.TrimSuffix(path.Base(strings.ReplaceAll(original, `\`, "/")), path.Ext(original))
	base = strings.Map(func(r rune) rune {
		switch {
		case r < unicode.MaxASCII && (unicode.IsLetter(r) || unicode.IsDigit(r)), r == '-', r == '_':
			return r
		case strings.ContainsRune("åäö", unicode.ToLower(r)):
			return map[rune]rune{'å': 'a', 'ä': 'a', 'ö': 'o', 'Å': 'A', 'Ä': 'A', 'Ö': 'O'}[r]
		}
		return '-'
	}, base)
	base = strings.Trim(base, "-")
	if base == "" {
		base = "fil"
	}
	if len(base) > 60-len(ext) {
		base = base[:60-len(ext)]
	}
	return base + ext
}
