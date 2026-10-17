package serve

import (
	"bytes"
	"embed"
	"io/fs"
	"net/http"
	"path"
	"strings"
	"time"
)

// The site build output is copied into site/ before go build. The committed placeholder
// index.html carries siteMarker, which keeps the handler in "not embedded" mode.
//
//go:embed all:site
var siteEmbed embed.FS

const siteMarker = "workflow-analytics-placeholder"

// siteFS is the site root. Tests replace it with an fstest.MapFS.
var siteFS fs.FS = func() fs.FS {
	sub, err := fs.Sub(siteEmbed, "site")
	if err != nil {
		panic(err)
	}
	return sub
}()

// siteHandler serves the analytics site from fsys. The mode is decided once, here.
// Paths under /v1 are never served as HTML.
func siteHandler(fsys fs.FS) http.HandlerFunc {
	index, err := fs.ReadFile(fsys, "index.html")
	embedded := err == nil && !bytes.Contains(index, []byte(siteMarker))
	return func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/v1" || strings.HasPrefix(r.URL.Path, "/v1/") {
			writeJSON(w, 404, map[string]string{"error": "not found"})
			return
		}
		if !embedded {
			writeJSON(w, 404, map[string]string{"error": "analytics bundle not embedded"})
			return
		}
		if r.Method != http.MethodGet && r.Method != http.MethodHead {
			w.Header().Set("Allow", "GET, HEAD")
			writeJSON(w, 405, map[string]string{"error": "method not allowed"})
			return
		}
		name := strings.TrimPrefix(path.Clean("/"+r.URL.Path), "/")
		if name != "" && name != "index.html" {
			if fi, err := fs.Stat(fsys, name); err == nil && fi.Mode().IsRegular() {
				if data, err := fs.ReadFile(fsys, name); err == nil {
					if strings.HasPrefix(name, "_app/immutable/") {
						w.Header().Set("Cache-Control", "public, max-age=31536000, immutable")
					}
					http.ServeContent(w, r, name, fi.ModTime(), bytes.NewReader(data))
					return
				}
			}
		}
		h := w.Header()
		h.Set("Content-Type", "text/html; charset=utf-8")
		h.Set("Cache-Control", "no-cache")
		http.ServeContent(w, r, "index.html", time.Time{}, bytes.NewReader(index))
	}
}
