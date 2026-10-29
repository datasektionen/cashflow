package claims

import (
	"context"
	"sync"
	"testing"

	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

// Two treasurers paying out the same expense at the same moment must not
// both succeed: that would be two bank transfers for one receipt.
func TestConcurrentPayoutsPayOnce(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	f.profile("kassor")
	treasurer := viewer("kassor", map[string]hive.Grant{perm.Pay: all, perm.Attest: all})

	for round := range 20 {
		n := f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, parts: []partSpec{{"Ada", 100, true}}})
		var wg sync.WaitGroup
		results := make([]error, 2)
		start := make(chan struct{})
		for i := range results {
			wg.Go(func() {
				<-start
				_, results[i] = s.CreatePayout(ctx, treasurer, []int64{n})
			})
		}
		close(start)
		wg.Wait()
		if results[0] == nil && results[1] == nil {
			var payments int
			f.pool.QueryRow(ctx, `SELECT count(*) FROM expenses_payment`).Scan(&payments)
			t.Fatalf("round %d: both payouts succeeded (%d payments recorded)", round, payments)
		}
	}
}
