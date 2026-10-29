package fortnox

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"sync"
)

// Fake is an in-memory Fortnox for development and tests: the OAuth server
// under /oauth-v1 (which approves at once) and the parts of the REST API
// under /3 that Cashflow uses. Refresh tokens rotate as Fortnox's do.
type Fake struct {
	mu          sync.Mutex
	next        int
	codes       map[string]bool
	access      map[string]bool
	refresh     map[string]bool
	Accounts    []Account
	CostCentres []CostCentre
	Series      []VoucherSeries
	// Vouchers by series, numbered from 1.
	Vouchers map[string][]FakeVoucher
	// Refreshes counts token refreshes, for tests.
	Refreshes int
}

type FakeVoucher struct {
	Number int
	NewVoucher
}

// NewFake returns a fake with a small chart of accounts and cost centres
// that match the seed data.
func NewFake() *Fake {
	return &Fake{
		codes: map[string]bool{}, access: map[string]bool{}, refresh: map[string]bool{},
		Accounts: []Account{
			{1930, "Företagskonto"}, {2440, "Leverantörsskulder"}, {2820, "Skulder till medlemmar"},
			{4010, "Inköp av varor"}, {5410, "Förbrukningsinventarier"}, {5460, "Förbrukningsmaterial"},
			{5800, "Resekostnader"}, {5831, "Kost och logi"}, {6071, "Representation"}, {6250, "Porto"},
			{6540, "IT-tjänster"}, {6990, "Övriga externa kostnader"},
		},
		CostCentres: []CostCentre{
			{"SLG", "Sektionslokalsgruppen"}, {"MOTT", "Mottagningen 2026"}, {"ADA", "Ada"},
			{"NLG", "Näringslivsgruppen"}, {"SN", "Studienämnden"}, {"DSYS", "Systemansvarig"}, {"STYR", "Styrelsen"},
		},
		Series: []VoucherSeries{
			{"A", "Redovisning"}, {"E", "Utlägg"}, {"U", "Leverantörsfakturor"}, {"M", "Manuella"},
		},
		Vouchers: map[string][]FakeVoucher{},
	}
}

func (f *Fake) issue() tokens {
	f.next++
	t := tokens{
		AccessToken:  fmt.Sprintf("fake-access-%d", f.next),
		RefreshToken: fmt.Sprintf("fake-refresh-%d", f.next),
		ExpiresIn:    3600,
	}
	f.access[t.AccessToken] = true
	f.refresh[t.RefreshToken] = true
	return t
}

func (f *Fake) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	f.mu.Lock()
	defer f.mu.Unlock()
	switch {
	case r.URL.Path == "/oauth-v1/auth":
		f.authorize(w, r)
	case r.URL.Path == "/oauth-v1/token":
		f.token(w, r)
	case strings.HasPrefix(r.URL.Path, "/3/"):
		if !f.access[strings.TrimPrefix(r.Header.Get("Authorization"), "Bearer ")] {
			fakeError(w, http.StatusUnauthorized, 2000311, "Ogiltig åtkomsttoken")
			return
		}
		f.api(w, r, strings.TrimPrefix(r.URL.Path, "/3"))
	default:
		http.NotFound(w, r)
	}
}

// authorize approves at once and sends the browser back with a code.
func (f *Fake) authorize(w http.ResponseWriter, r *http.Request) {
	redirect, err := url.Parse(r.URL.Query().Get("redirect_uri"))
	if err != nil || redirect.Host == "" {
		http.Error(w, "redirect_uri required", http.StatusBadRequest)
		return
	}
	f.next++
	code := fmt.Sprintf("fake-code-%d", f.next)
	f.codes[code] = true
	q := redirect.Query()
	q.Set("code", code)
	q.Set("state", r.URL.Query().Get("state"))
	redirect.RawQuery = q.Encode()
	http.Redirect(w, r, redirect.String(), http.StatusFound)
}

func (f *Fake) token(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	var ok bool
	switch r.PostForm.Get("grant_type") {
	case "authorization_code":
		code := r.PostForm.Get("code")
		ok = f.codes[code]
		delete(f.codes, code)
	case "refresh_token":
		token := r.PostForm.Get("refresh_token")
		ok = f.refresh[token]
		delete(f.refresh, token)
		if ok {
			f.Refreshes++
		}
	}
	w.Header().Set("Content-Type", "application/json")
	if !ok {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "invalid_grant", "error_description": "Invalid code or refresh token"})
		return
	}
	json.NewEncoder(w).Encode(f.issue())
}

func (f *Fake) api(w http.ResponseWriter, r *http.Request, path string) {
	switch {
	case r.Method == http.MethodGet && path == "/accounts":
		var items []map[string]any
		for _, a := range f.Accounts {
			items = append(items, map[string]any{"Number": a.Number, "Description": a.Description, "Active": true})
		}
		fakeList(w, "Accounts", items)
	case r.Method == http.MethodGet && path == "/costcenters":
		var items []map[string]any
		for _, cc := range f.CostCentres {
			items = append(items, map[string]any{"Code": cc.Code, "Description": cc.Description, "Active": true})
		}
		fakeList(w, "CostCenters", items)
	case r.Method == http.MethodGet && path == "/voucherseries":
		fakeList(w, "VoucherSeriesCollection", f.Series)
	case r.Method == http.MethodGet && strings.HasPrefix(path, "/vouchers/sublist/"):
		series := strings.TrimPrefix(path, "/vouchers/sublist/")
		items := []map[string]any{}
		for _, v := range f.Vouchers[series] {
			items = append(items, map[string]any{"VoucherNumber": v.Number, "VoucherSeries": series, "Description": v.Description})
		}
		fakeList(w, "Vouchers", items)
	case r.Method == http.MethodGet && strings.HasPrefix(path, "/vouchers/"):
		series, number, _ := strings.Cut(strings.TrimPrefix(path, "/vouchers/"), "/")
		n, _ := strconv.Atoi(number)
		for _, v := range f.Vouchers[series] {
			if v.Number == n {
				json.NewEncoder(w).Encode(map[string]any{"Voucher": map[string]any{"VoucherNumber": n, "VoucherSeries": series, "Description": v.Description}})
				return
			}
		}
		fakeError(w, http.StatusNotFound, codeNotFound, "Kan inte hitta verifikationen.")
	case r.Method == http.MethodPost && path == "/vouchers":
		f.createVoucher(w, r)
	default:
		fakeError(w, http.StatusNotFound, codeNotFound, "Unknown endpoint")
	}
}

func (f *Fake) createVoucher(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Voucher struct {
			VoucherSeries, Description, TransactionDate string
			VoucherRows                                 []struct {
				Account       int
				CostCenter    string
				Debit, Credit float64
			}
		}
	}
	if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
		fakeError(w, http.StatusBadRequest, 2001392, "Ogiltig data")
		return
	}
	v := body.Voucher
	known := false
	for _, s := range f.Series {
		known = known || s.Code == v.VoucherSeries
	}
	if !known {
		fakeError(w, http.StatusBadRequest, 2001939, "Ogiltig verifikationsserie")
		return
	}
	var debit, credit int64
	created := FakeVoucher{NewVoucher: NewVoucher{Series: v.VoucherSeries, Description: v.Description, TransactionDate: v.TransactionDate}}
	for _, row := range v.VoucherRows {
		valid := false
		for _, a := range f.Accounts {
			valid = valid || a.Number == row.Account
		}
		if !valid {
			fakeError(w, http.StatusBadRequest, 2001798, fmt.Sprintf("Kontot %d finns inte", row.Account))
			return
		}
		d, c := int64(row.Debit*100+0.5), int64(row.Credit*100+0.5)
		debit, credit = debit+d, credit+c
		created.Rows = append(created.Rows, VoucherRow{Account: row.Account, CostCentre: row.CostCenter, Debit: Kronor(d), Credit: Kronor(c)})
	}
	if len(v.VoucherRows) == 0 || debit != credit {
		fakeError(w, http.StatusBadRequest, 2000588, "Verifikationen är inte balanserad")
		return
	}
	created.Number = len(f.Vouchers[v.VoucherSeries]) + 1
	f.Vouchers[v.VoucherSeries] = append(f.Vouchers[v.VoucherSeries], created)
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]any{"Voucher": map[string]any{"VoucherNumber": created.Number, "VoucherSeries": v.VoucherSeries}})
}

func fakeList(w http.ResponseWriter, key string, items any) {
	json.NewEncoder(w).Encode(map[string]any{
		"MetaInformation": map[string]int{"@TotalPages": 1, "@CurrentPage": 1},
		key:               items,
	})
}

func fakeError(w http.ResponseWriter, status, code int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]any{"ErrorInformation": map[string]any{"error": 1, "message": message, "code": code}})
}

// VoucherCount returns how many vouchers the fake has booked in a series.
func (f *Fake) VoucherCount(series string) int {
	f.mu.Lock()
	defer f.mu.Unlock()
	return len(f.Vouchers[series])
}

// AddVoucher books a voucher directly, as someone working in Fortnox would.
func (f *Fake) AddVoucher(v NewVoucher) int {
	f.mu.Lock()
	defer f.mu.Unlock()
	n := len(f.Vouchers[v.Series]) + 1
	f.Vouchers[v.Series] = append(f.Vouchers[v.Series], FakeVoucher{Number: n, NewVoucher: v})
	return n
}
