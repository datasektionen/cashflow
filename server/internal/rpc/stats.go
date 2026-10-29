package rpc

import (
	"cmp"
	"context"
	"errors"
	"slices"
	"time"

	"connectrpc.com/connect"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgtype"

	claimv1 "github.com/datasektionen/cashflow/server/gen/cashflow/claim/v1"
	statsv1 "github.com/datasektionen/cashflow/server/gen/cashflow/stats/v1"
	"github.com/datasektionen/cashflow/server/internal/database/db"
)

// StatsService ports Cashflow 3's stats app.
type StatsService struct {
	Queries *db.Queries
}

const leaderboardSize = 20

func pgDate(t time.Time) pgtype.Date { return pgtype.Date{Time: t, Valid: true} }

func (s *StatsService) GetYear(ctx context.Context, req *connect.Request[statsv1.GetYearRequest]) (*connect.Response[statsv1.GetYearResponse], error) {
	year := int(req.Msg.Year)
	if this := time.Now().In(stockholm).Year(); year < 2000 || year > this {
		year = this
	}
	rows, err := s.Queries.MonthlyStats(ctx, db.MonthlyStatsParams{
		FromDate: pgDate(time.Date(year, 1, 1, 0, 0, 0, 0, time.UTC)),
		ToDate:   pgDate(time.Date(year+1, 1, 1, 0, 0, 0, 0, time.UTC)),
	})
	if err != nil {
		return nil, err
	}
	res := &statsv1.GetYearResponse{Year: int32(year)}
	for m := 1; m <= 12; m++ {
		res.Months = append(res.Months, &statsv1.Month{Month: int32(m)})
	}
	for _, r := range rows {
		m := res.Months[r.Month-1]
		if r.Kind == "invoice" {
			m.InvoiceCount, m.InvoiceTotalOre = r.Claims, r.TotalOre
		} else {
			m.ExpenseCount, m.ExpenseTotalOre = r.Claims, r.TotalOre
		}
	}
	return connect.NewResponse(res), nil
}

// periodStart is where a period begins, in Swedish time.
func periodStart(p statsv1.Period) time.Time {
	y, m, _ := time.Now().In(stockholm).Date()
	switch p {
	case statsv1.Period_PERIOD_YEAR:
		return time.Date(y, 1, 1, 0, 0, 0, 0, time.UTC)
	case statsv1.Period_PERIOD_MONTH:
		return time.Date(y, m, 1, 0, 0, 0, 0, time.UTC)
	}
	return time.Date(2000, 1, 1, 0, 0, 0, 0, time.UTC)
}

// ranked is the leaderboard in order, by total (capped) or by count, ties
// broken by the other and then by name.
func ranked(rows []db.ExpenseTotalsByOwnerRow, byCount bool) []db.ExpenseTotalsByOwnerRow {
	rows = slices.Clone(rows)
	slices.SortFunc(rows, func(a, b db.ExpenseTotalsByOwnerRow) int {
		byTotal := cmp.Compare(b.CappedTotalOre, a.CappedTotalOre)
		byNumber := cmp.Compare(b.Expenses, a.Expenses)
		if byCount {
			return cmp.Or(byNumber, byTotal, cmp.Compare(a.Name, b.Name))
		}
		return cmp.Or(byTotal, byNumber, cmp.Compare(a.Name, b.Name))
	})
	return rows
}

func (s *StatsService) GetLeaderboard(ctx context.Context, req *connect.Request[statsv1.GetLeaderboardRequest]) (*connect.Response[statsv1.GetLeaderboardResponse], error) {
	rows, err := s.Queries.ExpenseTotalsByOwner(ctx, pgDate(periodStart(req.Msg.Period)))
	if err != nil {
		return nil, err
	}
	byCount := req.Msg.Ranking == statsv1.Ranking_RANKING_COUNT
	res := &statsv1.GetLeaderboardResponse{}
	for i, r := range ranked(rows, byCount) {
		if i == leaderboardSize {
			break
		}
		res.Entries = append(res.Entries, &statsv1.LeaderboardEntry{
			Rank:     int32(i + 1),
			Person:   &claimv1.Person{Username: r.Username, Name: r.Name},
			TotalOre: r.CappedTotalOre,
			Count:    r.Expenses,
		})
	}
	return connect.NewResponse(res), nil
}

// GetPersonalStats ports UserLeaderboardView: the person's total counts every
// expense, while their places compare the leaderboard's capped totals.
// Equal totals share a place.
func (s *StatsService) GetPersonalStats(ctx context.Context, req *connect.Request[statsv1.GetPersonalStatsRequest]) (*connect.Response[statsv1.GetPersonalStatsResponse], error) {
	username := req.Msg.Username
	if username == "" {
		username = callerFrom(ctx).user.Username
	} else if _, err := s.Queries.GetUser(ctx, username); errors.Is(err, pgx.ErrNoRows) {
		return nil, connect.NewError(connect.CodeNotFound, errors.New("no such user"))
	} else if err != nil {
		return nil, err
	}
	rows, err := s.Queries.ExpenseTotalsByOwner(ctx, pgDate(periodStart(req.Msg.Period)))
	if err != nil {
		return nil, err
	}
	res := &statsv1.GetPersonalStatsResponse{People: int32(len(rows))}
	i := slices.IndexFunc(rows, func(r db.ExpenseTotalsByOwnerRow) bool { return r.Username == username })
	if i < 0 {
		return connect.NewResponse(res), nil
	}
	me := rows[i]
	res.TotalOre, res.Count = me.TotalOre, me.Expenses
	res.TotalRank, res.CountRank = 1, 1
	for _, r := range rows {
		if r.CappedTotalOre > me.CappedTotalOre {
			res.TotalRank++
		}
		if r.Expenses > me.Expenses {
			res.CountRank++
		}
	}
	return connect.NewResponse(res), nil
}
