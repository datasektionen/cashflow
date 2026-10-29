// Package budget reads Datasektionen's budget from GOrdian: cost centres,
// their secondary cost centres and budget lines. The whole tree is small, so
// it is kept in memory and refreshed in the background, replacing Cashflow
// 3's Django cache and warm_gordian_cache command.
package budget

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"

	"golang.org/x/sync/errgroup"
)

type CostCentre struct {
	ID        int
	Name      string
	Type      string // committee, partition, project, projectX or other
	Secondary []SecondaryCostCentre
}

type SecondaryCostCentre struct {
	ID    int
	Name  string
	Lines []Line
}

type Line struct {
	ID       int
	Name     string
	Accounts []int
	// Budgeted income and expense in öre, both positive. GOrdian stores
	// expenses as negative kronor; 0 means the line has no budget.
	IncomeOre  int64
	ExpenseOre int64
	Comment    string
}

var ErrUnavailable = errors.New("budget: GOrdian has not answered yet")

const refreshEvery = 12 * time.Hour

type Client struct {
	baseURL string
	http    *http.Client

	mu      sync.RWMutex
	tree    []CostCentre
	fetched time.Time
}

func NewClient(baseURL string) *Client {
	return &Client{baseURL: strings.TrimSuffix(baseURL, "/"), http: &http.Client{Timeout: 15 * time.Second}}
}

// Tree returns the budget. Before the first successful fetch it fetches
// synchronously; afterwards it returns the cached copy.
func (c *Client) Tree(ctx context.Context) ([]CostCentre, error) {
	c.mu.RLock()
	tree := c.tree
	c.mu.RUnlock()
	if tree != nil {
		return tree, nil
	}
	if err := c.Refresh(ctx); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrUnavailable, err)
	}
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.tree, nil
}

// Run keeps the tree fresh until ctx ends. A failed refresh keeps serving
// the previous tree.
func (c *Client) Run(ctx context.Context) {
	for {
		if err := c.Refresh(ctx); err != nil && ctx.Err() == nil {
			slog.Warn("budget refresh failed; serving the previous budget", "error", err)
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(refreshEvery):
		}
	}
}

// Refresh fetches the whole tree: one request for cost centres, then one per
// cost centre and one per secondary cost centre, a few at a time.
func (c *Client) Refresh(ctx context.Context) error {
	var ccs []struct {
		ID   int    `json:"CostCentreID"`
		Name string `json:"CostCentreName"`
		Type string `json:"CostCentreType"`
	}
	if err := c.get(ctx, "/api/CostCentres", nil, &ccs); err != nil {
		return err
	}
	tree := make([]CostCentre, len(ccs))
	g, gctx := errgroup.WithContext(ctx)
	g.SetLimit(8)
	for i, cc := range ccs {
		tree[i] = CostCentre{ID: cc.ID, Name: cc.Name, Type: costCentreType(cc.Type)}
		g.Go(func() error {
			secondary, err := c.secondary(gctx, cc.ID)
			tree[i].Secondary = secondary
			return err
		})
	}
	if err := g.Wait(); err != nil {
		return err
	}
	c.mu.Lock()
	c.tree, c.fetched = tree, time.Now()
	c.mu.Unlock()
	slog.Info("budget loaded from GOrdian", "cost_centres", len(tree))
	return nil
}

func (c *Client) secondary(ctx context.Context, ccID int) ([]SecondaryCostCentre, error) {
	var sccs []struct {
		ID   int    `json:"SecondaryCostCentreID"`
		Name string `json:"SecondaryCostCentreName"`
	}
	if err := c.get(ctx, "/api/SecondaryCostCentres", url.Values{"id": {strconv.Itoa(ccID)}}, &sccs); err != nil {
		return nil, err
	}
	out := make([]SecondaryCostCentre, len(sccs))
	for i, scc := range sccs {
		var lines []struct {
			ID      int    `json:"BudgetLineID"`
			Name    string `json:"BudgetLineName"`
			Account string `json:"BudgetLineAccount"`
			Income  int64  `json:"BudgetLineIncome"`
			Expense int64  `json:"BudgetLineExpense"`
			Comment string `json:"BudgetLineComment"`
		}
		// GOrdian answers "null" for a secondary cost centre without lines.
		if err := c.get(ctx, "/api/BudgetLines", url.Values{"id": {strconv.Itoa(scc.ID)}}, &lines); err != nil {
			return nil, err
		}
		out[i] = SecondaryCostCentre{ID: scc.ID, Name: scc.Name}
		for _, l := range lines {
			out[i].Lines = append(out[i].Lines, Line{
				ID: l.ID, Name: l.Name, Accounts: ParseAccounts(l.Account),
				IncomeOre: abs(l.Income) * 100, ExpenseOre: abs(l.Expense) * 100, Comment: l.Comment,
			})
		}
	}
	return out, nil
}

func (c *Client) get(ctx context.Context, path string, query url.Values, into any) error {
	u := c.baseURL + path
	if query != nil {
		u += "?" + query.Encode()
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return err
	}
	res, err := c.http.Do(req)
	if err != nil {
		return fmt.Errorf("gordian %s: %w", path, err)
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		return fmt.Errorf("gordian %s: %s", path, res.Status)
	}
	return json.NewDecoder(res.Body).Decode(into)
}

func costCentreType(t string) string {
	switch t {
	case "committee", "partition", "project", "projectX":
		return t
	}
	return "other"
}

func abs(n int64) int64 {
	if n < 0 {
		return -n
	}
	return n
}

var (
	accountList  = regexp.MustCompile(`^\d{4}(, ?\d{4})*$`)
	accountRange = regexp.MustCompile(`^(\d{4})-(\d{4})$`)
)

// ParseAccounts reads GOrdian's account field: "4209", "3041, 3042",
// "3021-3025" or "". Ranges include both ends (Cashflow 3 left out the
// last account). Anything else is treated as no accounts, as Cashflow 3 did.
func ParseAccounts(s string) []int {
	s = strings.TrimSpace(s)
	switch {
	case accountList.MatchString(s):
		var out []int
		for _, part := range strings.Split(s, ",") {
			n, _ := strconv.Atoi(strings.TrimSpace(part))
			out = append(out, n)
		}
		return out
	case accountRange.MatchString(s):
		m := accountRange.FindStringSubmatch(s)
		from, _ := strconv.Atoi(m[1])
		to, _ := strconv.Atoi(m[2])
		var out []int
		for n := from; n <= to; n++ {
			out = append(out, n)
		}
		return out
	}
	return nil
}

// Find returns the budget line a claim part names, matching names as
// Cashflow 3 does but forgiving case and spacing; nil when there is none.
func Find(tree []CostCentre, costCentre, secondary, line string) *Line {
	for _, cc := range tree {
		if !sameName(cc.Name, costCentre) {
			continue
		}
		for _, scc := range cc.Secondary {
			if !sameName(scc.Name, secondary) {
				continue
			}
			for i, l := range scc.Lines {
				if sameName(l.Name, line) {
					return &scc.Lines[i]
				}
			}
		}
	}
	return nil
}

func sameName(a, b string) bool {
	return strings.EqualFold(strings.Join(strings.Fields(a), " "), strings.Join(strings.Fields(b), " "))
}
