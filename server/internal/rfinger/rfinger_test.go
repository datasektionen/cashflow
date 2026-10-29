package rfinger

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"slices"
	"testing"
)

func TestPicturesBatchAndCache(t *testing.T) {
	var batches [][]string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer key" || r.URL.Path != "/api/batch" {
			http.Error(w, "no", http.StatusUnauthorized)
			return
		}
		var names []string
		json.NewDecoder(r.Body).Decode(&names)
		batches = append(batches, names)
		out := map[string]string{}
		for _, n := range names {
			out[n] = "https://pics/" + n
		}
		json.NewEncoder(w).Encode(out)
	}))
	defer srv.Close()

	c := NewClient(srv.URL, "key")
	got, err := c.Pictures(context.Background(), []string{"ture", "diana", "ture"})
	if err != nil || got["ture"] != "https://pics/ture" || len(got) != 2 {
		t.Fatalf("got %v, %v", got, err)
	}
	if _, err := c.Pictures(context.Background(), []string{"diana", "martin"}); err != nil {
		t.Fatal(err)
	}
	if len(batches) != 2 || !slices.Equal(batches[1], []string{"martin"}) {
		t.Errorf("cached names must not be fetched again: %v", batches)
	}
}

func TestNoKeyMeansNoPictures(t *testing.T) {
	got, err := NewClient("http://unused", "").Pictures(context.Background(), []string{"ture"})
	if err != nil || len(got) != 0 {
		t.Errorf("got %v, %v", got, err)
	}
}
