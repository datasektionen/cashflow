package rpc

import (
	"slices"
	"testing"

	"github.com/datasektionen/cashflow/server/internal/database/db"
)

func TestRanked(t *testing.T) {
	rows := []db.ExpenseTotalsByOwnerRow{
		{Username: "a", Name: "Anna", CappedTotalOre: 100, Expenses: 5},
		{Username: "b", Name: "Bertil", CappedTotalOre: 300, Expenses: 1},
		{Username: "c", Name: "Cecilia", CappedTotalOre: 100, Expenses: 7},
	}
	names := func(rs []db.ExpenseTotalsByOwnerRow) (out []string) {
		for _, r := range rs {
			out = append(out, r.Username)
		}
		return out
	}
	if got := names(ranked(rows, false)); !slices.Equal(got, []string{"b", "c", "a"}) {
		t.Errorf("by total, ties by count: %v", got)
	}
	if got := names(ranked(rows, true)); !slices.Equal(got, []string{"c", "a", "b"}) {
		t.Errorf("by count: %v", got)
	}
}
