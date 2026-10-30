// Package fortnox talks to Fortnox, the bookkeeping system, through one
// service account that the treasurer connects with OAuth. It ports Cashflow
// 3's fortnox app: the API client, the token refresh and the cached lists of
// accounts and cost centres.
package fortnox

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"math"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/datasektionen/cashflow/server/internal/database/db"
)

type Config struct {
	ClientID     string
	ClientSecret string
	// APIURL is the REST API, AuthURL the OAuth server; both point at the
	// fake (cmd/fakefortnox) in development.
	APIURL  string
	AuthURL string
}

// Scopes are Cashflow 3's FORTNOX_SCOPE.
var Scopes = []string{"bookkeeping", "companyinformation", "settings", "customer", "profile", "costcenter"}

var (
	// ErrNotConnected: nobody has connected the service account, or Fortnox
	// revoked it.
	ErrNotConnected = errors.New("fortnox: not connected")
	ErrNotFound     = errors.New("fortnox: not found")
)

// APIError is an error Fortnox reported.
type APIError struct {
	Status  int
	Code    int
	Message string
}

func (e *APIError) Error() string {
	return fmt.Sprintf("fortnox: %d %s (code %d)", e.Status, e.Message, e.Code)
}

// Fortnox's error codes for a missing resource.
const codeNotFound = 2000423

type Account struct {
	Number      int
	Description string
}

type CostCentre struct {
	Code        string
	Description string
}

type VoucherSeries struct {
	Code        string
	Description string
}

// VoucherRow amounts are öre; Fortnox gets kronor.
type VoucherRow struct {
	Account    int    `json:"Account"`
	CostCentre string `json:"CostCenter,omitempty"`
	Debit      Kronor `json:"Debit,omitempty"`
	Credit     Kronor `json:"Credit,omitempty"`
}

type NewVoucher struct {
	Series          string       `json:"VoucherSeries"`
	Description     string       `json:"Description"`
	TransactionDate string       `json:"TransactionDate"`
	Rows            []VoucherRow `json:"VoucherRows"`
}

// Kronor is an amount in öre that Fortnox reads as a decimal number of kronor.
type Kronor int64

func (k Kronor) MarshalJSON() ([]byte, error) {
	sign, ore := "", int64(k)
	if ore < 0 {
		sign, ore = "-", -ore
	}
	return fmt.Appendf(nil, "%s%d.%02d", sign, ore/100, ore%100), nil
}

// Connection is who connected the service account and when.
type Connection struct {
	Username, Name string
	ConnectedAt    time.Time
}

const listTTL = 6 * time.Hour

type Client struct {
	cfg  Config
	pool *pgxpool.Pool
	http *http.Client

	mu          sync.Mutex
	accounts    cached[[]Account]
	costCentres cached[[]CostCentre]
}

type cached[T any] struct {
	value   T
	fetched time.Time
}

// New returns nil when Fortnox is not configured; the integration is then
// off, as with Cashflow 3's FORTNOX_ENABLED=false.
func New(cfg Config, pool *pgxpool.Pool) *Client {
	if cfg.ClientID == "" {
		return nil
	}
	cfg.APIURL = strings.TrimSuffix(cfg.APIURL, "/")
	cfg.AuthURL = strings.TrimSuffix(cfg.AuthURL, "/")
	return &Client{cfg: cfg, pool: pool, http: &http.Client{Timeout: 20 * time.Second}}
}

// Enabled reports whether the integration is on at all.
func (c *Client) Enabled() bool { return c != nil }

// ---- OAuth ----

// AuthCodeURL is where the treasurer approves Cashflow in Fortnox.
func (c *Client) AuthCodeURL(redirectURI, state string) string {
	q := url.Values{
		"client_id":     {c.cfg.ClientID},
		"redirect_uri":  {redirectURI},
		"scope":         {strings.Join(Scopes, " ")},
		"state":         {state},
		"access_type":   {"offline"},
		"response_type": {"code"},
		"account_type":  {"service"},
	}
	return c.cfg.AuthURL + "/auth?" + q.Encode()
}

type tokens struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	ExpiresIn    int    `json:"expires_in"`
	// Set instead when Fortnox refuses.
	Error            string `json:"error"`
	ErrorDescription string `json:"error_description"`
}

func (t tokens) expiresAt() pgtype.Timestamptz {
	return pgtype.Timestamptz{Time: time.Now().Add(time.Duration(t.ExpiresIn) * time.Second), Valid: true}
}

// errInvalidGrant: the refresh token is spent or revoked.
var errInvalidGrant = errors.New("fortnox: invalid grant")

func (c *Client) requestTokens(ctx context.Context, form url.Values) (tokens, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.cfg.AuthURL+"/token", strings.NewReader(form.Encode()))
	if err != nil {
		return tokens{}, err
	}
	credentials := base64.StdEncoding.EncodeToString([]byte(c.cfg.ClientID + ":" + c.cfg.ClientSecret))
	req.Header.Set("Authorization", "Basic "+credentials)
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	res, err := c.http.Do(req)
	if err != nil {
		return tokens{}, fmt.Errorf("fortnox token: %w", err)
	}
	defer res.Body.Close()
	var t tokens
	if err := json.NewDecoder(res.Body).Decode(&t); err != nil {
		return tokens{}, fmt.Errorf("fortnox token: %s: %w", res.Status, err)
	}
	switch {
	case t.Error == "invalid_grant":
		return tokens{}, errInvalidGrant
	case t.Error != "" || t.AccessToken == "":
		return tokens{}, fmt.Errorf("fortnox token: %s: %s %s", res.Status, t.Error, t.ErrorDescription)
	}
	return t, nil
}

// Connect exchanges the code from the OAuth redirect for tokens and makes
// them the service account, replacing any previous connection.
func (c *Client) Connect(ctx context.Context, username, code, redirectURI string) error {
	t, err := c.requestTokens(ctx, url.Values{
		"grant_type": {"authorization_code"}, "code": {code}, "redirect_uri": {redirectURI},
	})
	if err != nil {
		return err
	}
	err = pgx.BeginFunc(ctx, c.pool, func(tx pgx.Tx) error {
		q := db.New(tx)
		if err := q.DeleteFortnoxTokens(ctx); err != nil {
			return err
		}
		return q.InsertFortnoxTokens(ctx, db.InsertFortnoxTokensParams{
			AccessToken: t.AccessToken, RefreshToken: t.RefreshToken, ExpiresAt: t.expiresAt(), Username: username,
		})
	})
	if err == nil {
		c.forgetLists()
		slog.Info("fortnox connected", "by", username)
	}
	return err
}

// Disconnect forgets the service account's tokens.
func (c *Client) Disconnect(ctx context.Context) error {
	c.forgetLists()
	return db.New(c.pool).DeleteFortnoxTokens(ctx)
}

// Connection returns who connected Fortnox, or nil when it is not connected.
func (c *Client) Connection(ctx context.Context) (*Connection, error) {
	row, err := db.New(c.pool).GetFortnoxConnection(ctx)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, nil
	} else if err != nil {
		return nil, err
	}
	return &Connection{Username: row.Username, Name: row.Name, ConnectedAt: row.CreatedAt.Time}, nil
}

// Check asks Fortnox whether the connection works, with a cheap call. A
// connection Fortnox no longer accepts is forgotten on the way (see token),
// so Connection reports it gone afterwards.
func (c *Client) Check(ctx context.Context) error {
	_, err := c.VoucherSeries(ctx)
	return err
}

// token returns a valid access token, refreshing it under the row lock when
// it is about to expire, as Cashflow 3's retrieve_or_refresh_token. A
// refused refresh means the connection is gone and the row is deleted.
func (c *Client) token(ctx context.Context, minValidity time.Duration) (string, error) {
	var access string
	revoked := false
	err := pgx.BeginFunc(ctx, c.pool, func(tx pgx.Tx) error {
		q := db.New(tx)
		row, err := q.LockFortnoxTokens(ctx)
		if errors.Is(err, pgx.ErrNoRows) {
			return ErrNotConnected
		} else if err != nil {
			return err
		}
		if time.Until(row.ExpiresAt.Time) > minValidity {
			access = row.AccessToken
			return nil
		}
		t, err := c.requestTokens(ctx, url.Values{
			"grant_type": {"refresh_token"}, "refresh_token": {row.RefreshToken}, "client_id": {c.cfg.ClientID},
		})
		if errors.Is(err, errInvalidGrant) {
			slog.Error("fortnox refused the refresh token; disconnecting")
			revoked = true
			return q.DeleteFortnoxTokens(ctx)
		} else if err != nil {
			return err
		}
		access = t.AccessToken
		return q.UpdateFortnoxTokens(ctx, db.UpdateFortnoxTokensParams{
			ID: row.ID, AccessToken: t.AccessToken, RefreshToken: t.RefreshToken, ExpiresAt: t.expiresAt(),
		})
	})
	if err == nil && revoked {
		// Reported after the transaction, so that the deletion commits.
		return "", ErrNotConnected
	}
	return access, err
}

// KeepAlive refreshes the tokens before they expire until ctx ends. Fortnox
// refresh tokens lapse when unused, so an idle month would otherwise
// disconnect Cashflow; this replaces Cashflow 3's refresh_fortnox_token cron.
func (c *Client) KeepAlive(ctx context.Context) {
	for {
		if _, err := c.token(ctx, 20*time.Minute); err != nil && !errors.Is(err, ErrNotConnected) && ctx.Err() == nil {
			slog.Warn("fortnox token refresh failed", "error", err)
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(10 * time.Minute):
		}
	}
}

// ---- REST API ----

// forceRefresh as a token's minimum validity always refreshes it.
const forceRefresh = time.Duration(math.MaxInt64)

// do calls the API. A refused access token is refreshed and the call tried
// once more: Fortnox may revoke tokens early, and a refused refresh then
// disconnects for real rather than leaving a connection that never works.
func (c *Client) do(ctx context.Context, method, path string, body, into any) error {
	var payload []byte
	if body != nil {
		var err error
		if payload, err = json.Marshal(body); err != nil {
			return err
		}
	}
	access, err := c.token(ctx, time.Minute)
	if err != nil {
		return err
	}
	status, raw, err := c.send(ctx, method, path, payload, access)
	if err == nil && status == http.StatusUnauthorized {
		if access, err = c.token(ctx, forceRefresh); err != nil {
			return err
		}
		status, raw, err = c.send(ctx, method, path, payload, access)
	}
	if err != nil {
		return err
	}
	if status >= 300 {
		return parseError(status, raw)
	}
	if err := json.Unmarshal(raw, into); err != nil {
		return fmt.Errorf("fortnox: %s %s: %w", method, path, err)
	}
	return nil
}

func (c *Client) send(ctx context.Context, method, path string, payload []byte, access string) (int, []byte, error) {
	var reader io.Reader
	if payload != nil {
		reader = bytes.NewReader(payload)
	}
	req, err := http.NewRequestWithContext(ctx, method, c.cfg.APIURL+path, reader)
	if err != nil {
		return 0, nil, err
	}
	req.Header.Set("Authorization", "Bearer "+access)
	req.Header.Set("Accept", "application/json")
	if payload != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	res, err := c.http.Do(req)
	if err != nil {
		return 0, nil, fmt.Errorf("fortnox: %w", err)
	}
	defer res.Body.Close()
	raw, err := io.ReadAll(io.LimitReader(res.Body, 16<<20))
	if err != nil {
		return 0, nil, fmt.Errorf("fortnox: %w", err)
	}
	return res.StatusCode, raw, nil
}

// parseError reads Fortnox's ErrorInformation, whose keys come in either
// case depending on the endpoint.
func parseError(status int, raw []byte) error {
	var envelope struct {
		Info map[string]json.RawMessage `json:"ErrorInformation"`
	}
	e := &APIError{Status: status, Message: http.StatusText(status)}
	if json.Unmarshal(raw, &envelope) == nil {
		for key, value := range envelope.Info {
			switch strings.ToLower(key) {
			case "message":
				_ = json.Unmarshal(value, &e.Message)
			case "code":
				_ = json.Unmarshal(value, &e.Code)
			}
		}
	}
	if status == http.StatusNotFound || e.Code == codeNotFound {
		return fmt.Errorf("%w: %s", ErrNotFound, e.Message)
	}
	if status == http.StatusUnauthorized {
		return fmt.Errorf("%w: %s", ErrNotConnected, e.Message)
	}
	return e
}

type meta struct {
	TotalPages int `json:"@TotalPages"`
}

// list fetches every page of a collection.
func list[T any](ctx context.Context, c *Client, path, key string) ([]T, error) {
	var all []T
	for page := 1; ; page++ {
		var res map[string]json.RawMessage
		if err := c.do(ctx, http.MethodGet, fmt.Sprintf("%s?limit=500&page=%d", path, page), nil, &res); err != nil {
			return nil, err
		}
		var items []T
		if err := json.Unmarshal(res[key], &items); err != nil {
			return nil, fmt.Errorf("fortnox: %s: %w", path, err)
		}
		all = append(all, items...)
		var m meta
		_ = json.Unmarshal(res["MetaInformation"], &m)
		if page >= m.TotalPages {
			return all, nil
		}
	}
}

func (c *Client) forgetLists() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.accounts, c.costCentres = cached[[]Account]{}, cached[[]CostCentre]{}
}

// Accounts are the active accounts in the chart of accounts, cached as in
// Cashflow 3.
func (c *Client) Accounts(ctx context.Context) ([]Account, error) {
	return remember(c, &c.accounts, func() ([]Account, error) {
		items, err := list[struct {
			Number      int
			Description string
			Active      bool
		}](ctx, c, "/accounts", "Accounts")
		var out []Account
		for _, a := range items {
			if a.Active {
				out = append(out, Account{Number: a.Number, Description: a.Description})
			}
		}
		return out, err
	})
}

// CostCentres are the active cost centres, cached.
func (c *Client) CostCentres(ctx context.Context) ([]CostCentre, error) {
	return remember(c, &c.costCentres, func() ([]CostCentre, error) {
		items, err := list[struct {
			Code        string
			Description string
			Active      bool
		}](ctx, c, "/costcenters", "CostCenters")
		var out []CostCentre
		for _, cc := range items {
			if cc.Active {
				out = append(out, CostCentre{Code: cc.Code, Description: cc.Description})
			}
		}
		return out, err
	})
}

func remember[T any](c *Client, slot *cached[T], fetch func() (T, error)) (T, error) {
	c.mu.Lock()
	if !slot.fetched.IsZero() && time.Since(slot.fetched) < listTTL {
		defer c.mu.Unlock()
		return slot.value, nil
	}
	c.mu.Unlock()
	value, err := fetch()
	if err != nil {
		var zero T
		return zero, err
	}
	c.mu.Lock()
	*slot = cached[T]{value: value, fetched: time.Now()}
	c.mu.Unlock()
	return value, nil
}

// VoucherSeries lists Fortnox's voucher series.
func (c *Client) VoucherSeries(ctx context.Context) ([]VoucherSeries, error) {
	return list[VoucherSeries](ctx, c, "/voucherseries", "VoucherSeriesCollection")
}

// VoucherExists reports whether a voucher exists in the current financial year.
func (c *Client) VoucherExists(ctx context.Context, series string, number int) (bool, error) {
	var res json.RawMessage
	err := c.do(ctx, http.MethodGet, "/vouchers/"+url.PathEscape(series)+"/"+strconv.Itoa(number), nil, &res)
	if errors.Is(err, ErrNotFound) {
		return false, nil
	}
	return err == nil, err
}

// FindVoucher returns the number of a voucher in the series with the
// description, if there is one.
// Cashflow writes a claim's number into the description, so this finds a
// voucher created for a claim that Cashflow failed to record.
func (c *Client) FindVoucher(ctx context.Context, series, description string) (int, bool, error) {
	vouchers, err := list[struct {
		Description   string
		VoucherNumber int
	}](ctx, c, "/vouchers/sublist/"+url.PathEscape(series), "Vouchers")
	if errors.Is(err, ErrNotFound) {
		return 0, false, nil
	} else if err != nil {
		return 0, false, err
	}
	for _, v := range vouchers {
		if v.Description == description {
			return v.VoucherNumber, true, nil
		}
	}
	return 0, false, nil
}

// CreateVoucher books a voucher and returns its number in the series.
func (c *Client) CreateVoucher(ctx context.Context, v NewVoucher) (int, error) {
	var res struct {
		Voucher struct{ VoucherNumber int }
	}
	if err := c.do(ctx, http.MethodPost, "/vouchers", map[string]NewVoucher{"Voucher": v}, &res); err != nil {
		return 0, err
	}
	if res.Voucher.VoucherNumber == 0 {
		return 0, errors.New("fortnox: created voucher has no number")
	}
	return res.Voucher.VoucherNumber, nil
}
