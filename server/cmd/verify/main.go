// Command verify reads every claim in the database the way Cashflow 4's
// pages do and checks that each receipt is in S3. It is the first thing to
// run on staging against a copy of production: anything it reports is data
// Cashflow 4 would show wrongly or not at all.
//
// It only reads: the database connection is read-only, and S3 is asked
// whether files exist without downloading them.
//
//	go run ./cmd/verify              # reads server/.env like the server
//	go run ./cmd/verify -files=false # skip S3
package main

import (
	"context"
	"flag"
	"fmt"
	"log/slog"
	"os"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/config"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
	"github.com/datasektionen/cashflow/server/internal/storage"
)

func main() {
	checkFiles := flag.Bool("files", true, "check that every file exists in S3")
	flag.Parse()
	problems, err := run(context.Background(), *checkFiles)
	if err != nil {
		slog.Error("verify failed", "error", err)
		os.Exit(2)
	}
	if problems > 0 {
		os.Exit(1)
	}
}

func run(ctx context.Context, checkFiles bool) (int, error) {
	if err := config.LoadDotEnv(".env"); err != nil {
		return 0, err
	}
	env, err := config.FromEnv()
	if err != nil {
		return 0, err
	}
	poolCfg, err := pgxpool.ParseConfig(env.DatabaseURL)
	if err != nil {
		return 0, err
	}
	// Read-only, whatever the code below does: this runs against production data.
	poolCfg.ConnConfig.RuntimeParams["default_transaction_read_only"] = "on"
	pool, err := pgxpool.NewWithConfig(ctx, poolCfg)
	if err != nil {
		return 0, err
	}
	defer pool.Close()
	var files *storage.Store
	if checkFiles {
		if files, err = storage.New(ctx, env.S3); err != nil {
			return 0, err
		}
	}

	store := claims.NewStore(pool, env.PublicURL)
	q := store.Queries
	everything := claims.Viewer{Username: "verify", Perms: perm.New("verify", hive.Permissions{perm.ViewAll: {All: true}})}

	var problems, count, fileCount int
	var total int64
	stages := map[claims.Stage]int{}
	report := func(c claims.Summary, format string, args ...any) {
		problems++
		fmt.Printf("%s #%d %q: %s\n", c.Kind, c.Number, c.Description, fmt.Sprintf(format, args...))
	}

	for page := 1; ; page++ {
		list, matching, err := store.List(ctx, everything, claims.Filter{Page: page, PageSize: claims.MaxPageSize, Sort: claims.SortCreated})
		if err != nil {
			return problems, fmt.Errorf("list page %d: %w", page, err)
		}
		for _, c := range list {
			count++
			total += c.AmountOre
			stages[c.Stage()]++

			parts, err := q.ListClaimParts(ctx, c.ID)
			if err != nil {
				report(c, "parts: %v", err)
				continue
			}
			var sum int64
			for _, p := range parts {
				sum += p.AmountOre
				if p.CostCentre == "" {
					report(c, "a part has no cost centre")
				}
			}
			if len(parts) == 0 {
				report(c, "no parts")
			}
			if sum != c.AmountOre {
				report(c, "parts add up to %d öre, the list says %d", sum, c.AmountOre)
			}
			if _, err := q.ListClaimComments(ctx, c.ID); err != nil {
				report(c, "comments: %v", err)
			}
			switch c.Kind {
			case claims.Expense:
				if _, err := q.GetExpenseDetails(ctx, c.ID); err != nil {
					report(c, "expense details: %v", err)
				}
			case claims.Invoice:
				if _, err := q.GetInvoiceDetails(ctx, c.ID); err != nil {
					report(c, "invoice details: %v", err)
				}
			default:
				report(c, "neither expense nor invoice")
			}
			if c.Date == nil {
				report(c, "no date")
			}

			list, err := q.ListClaimFiles(ctx, c.ID)
			if err != nil {
				report(c, "files: %v", err)
				continue
			}
			for _, f := range list {
				fileCount++
				if files == nil {
					continue
				}
				if ok, err := files.Exists(ctx, f.File); err != nil {
					report(c, "file %s: %v", f.File, err)
				} else if !ok {
					report(c, "file %s is not in S3", f.File)
				}
			}
		}
		if page*claims.MaxPageSize >= matching {
			break
		}
	}

	// Cross-check the totals against the tables, independently of the list query.
	var claimRows int
	var sqlTotal int64
	if err := pool.QueryRow(ctx, `SELECT (SELECT count(*) FROM core_claim), COALESCE((SELECT sum(amount) * 100 FROM core_claimpart), 0)::bigint`).
		Scan(&claimRows, &sqlTotal); err != nil && err != pgx.ErrNoRows {
		return problems, err
	}
	if claimRows != count {
		problems++
		fmt.Printf("the tables have %d claims, the list shows %d\n", claimRows, count)
	}
	if sqlTotal != total {
		problems++
		fmt.Printf("the parts add up to %d öre, the list to %d\n", sqlTotal, total)
	}

	fmt.Printf("\n%d claims, %d files%s, %d öre in total\n", count, fileCount, map[bool]string{true: " checked in S3", false: ""}[files != nil], total)
	for s := claims.StageSubmitted; s <= claims.StageAccounted; s++ {
		fmt.Printf("  stage %d: %d\n", s, stages[s])
	}
	fmt.Printf("%d problems\n", problems)
	return problems, nil
}
