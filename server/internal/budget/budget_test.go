package budget

import (
	"context"
	"net/http"
	"net/http/httptest"
	"slices"
	"testing"
)

func TestParseAccounts(t *testing.T) {
	for in, want := range map[string][]int{
		"4209":       {4209},
		"3041, 3042": {3041, 3042},
		"3041,3042":  {3041, 3042},
		"3021-3023":  {3021, 3022, 3023},
		"":           nil,
		"abc":        nil,
	} {
		if got := ParseAccounts(in); !slices.Equal(got, want) {
			t.Errorf("ParseAccounts(%q) = %v, want %v", in, got, want)
		}
	}
}

func TestTree(t *testing.T) {
	gordian := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path + "?" + r.URL.RawQuery {
		case "/api/CostCentres?":
			w.Write([]byte(`[{"CostCentreID":0,"CostCentreName":"Ada","CostCentreType":"committee"},{"CostCentreID":7,"CostCentreName":"Odd","CostCentreType":"weird"}]`))
		case "/api/SecondaryCostCentres?id=0":
			w.Write([]byte(`[{"CostCentreID":0,"SecondaryCostCentreID":3,"SecondaryCostCentreName":"Allmänt"}]`))
		case "/api/SecondaryCostCentres?id=7":
			w.Write([]byte(`[{"CostCentreID":7,"SecondaryCostCentreID":9,"SecondaryCostCentreName":"Tomt"}]`))
		case "/api/BudgetLines?id=3":
			w.Write([]byte(`[{"SecondaryCostCentreID":3,"BudgetLineID":1,"BudgetLineName":"Fika","BudgetLineAccount":"4045","BudgetLineIncome":0,"BudgetLineExpense":-2000,"BudgetLineComment":""}]`))
		case "/api/BudgetLines?id=9":
			w.Write([]byte(`null`))
		default:
			http.NotFound(w, r)
		}
	}))
	defer gordian.Close()

	tree, err := NewClient(gordian.URL).Tree(context.Background())
	if err != nil {
		t.Fatal(err)
	}
	if len(tree) != 2 || tree[1].Type != "other" || len(tree[1].Secondary[0].Lines) != 0 {
		t.Fatalf("tree %+v", tree)
	}
	line := tree[0].Secondary[0].Lines[0]
	if line.Name != "Fika" || line.ExpenseOre != 200000 || !slices.Equal(line.Accounts, []int{4045}) {
		t.Errorf("line %+v", line)
	}
}
