// Command fakefortnox serves an in-memory Fortnox for development on
// localhost:9004; point FORTNOX_API_URL and FORTNOX_AUTH_URL at it. Connecting
// approves at once, and vouchers live until it stops.
package main

import (
	"log/slog"
	"net/http"

	"github.com/datasektionen/cashflow/server/internal/fortnox"
)

func main() {
	slog.Info("fake Fortnox listening", "address", "localhost:9004")
	if err := http.ListenAndServe("localhost:9004", fortnox.NewFake()); err != nil {
		slog.Error("fake Fortnox stopped", "error", err)
	}
}
