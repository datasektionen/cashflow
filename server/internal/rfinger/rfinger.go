// Package rfinger fetches profile pictures from rfinger, Datasektionen's
// picture service, as Cashflow 3's cashflow/rfinger.py, caching each URL for
// 12 hours (PROFILE_PICTURE_CACHE_TIMEOUT).
package rfinger

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"slices"
	"sync"
	"time"
)

const ttl = 12 * time.Hour

type Client struct {
	baseURL string
	apiKey  string
	http    *http.Client

	mu    sync.Mutex
	cache map[string]entry
}

type entry struct {
	url     string
	fetched time.Time
}

// NewClient returns nil when there is no API key: pictures are optional, and
// users then show their initials.
func NewClient(baseURL, apiKey string) *Client {
	if apiKey == "" {
		return nil
	}
	return &Client{baseURL: baseURL, apiKey: apiKey, http: &http.Client{Timeout: 5 * time.Second}, cache: map[string]entry{}}
}

// Pictures returns a picture URL per username, from the cache when fresh and
// otherwise in one batch request.
func (c *Client) Pictures(ctx context.Context, usernames []string) (map[string]string, error) {
	out := map[string]string{}
	if c == nil {
		return out, nil
	}
	var missing []string
	c.mu.Lock()
	for _, u := range slices.Compact(slices.Sorted(slices.Values(usernames))) {
		if e, ok := c.cache[u]; ok && time.Since(e.fetched) < ttl {
			out[u] = e.url
		} else {
			missing = append(missing, u)
		}
	}
	c.mu.Unlock()
	if len(missing) == 0 {
		return out, nil
	}

	body, _ := json.Marshal(missing)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/api/batch", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.apiKey)
	req.Header.Set("Content-Type", "application/json")
	res, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("rfinger: %w", err)
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("rfinger: %s", res.Status)
	}
	var fetched map[string]string
	if err := json.NewDecoder(res.Body).Decode(&fetched); err != nil {
		return nil, fmt.Errorf("rfinger: %w", err)
	}
	now := time.Now()
	c.mu.Lock()
	for u, url := range fetched {
		c.cache[u] = entry{url: url, fetched: now}
		out[u] = url
	}
	c.mu.Unlock()
	return out, nil
}
