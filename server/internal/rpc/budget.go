package rpc

import (
	"context"
	"errors"
	"strings"
	"time"

	"connectrpc.com/connect"
	"github.com/jackc/pgx/v5/pgtype"

	budgetv1 "github.com/datasektionen/cashflow/server/gen/cashflow/budget/v1"
	"github.com/datasektionen/cashflow/server/internal/budget"
	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/database/db"
)

type BudgetService struct {
	Budget *budget.Client
	Store  *claims.Store
}

var stockholm, _ = time.LoadLocation("Europe/Stockholm")

// normaliseName matches cost centre, secondary cost centre and budget line
// names between GOrdian and claims, as Cashflow 3's budget views do.
func normaliseName(s string) string { return strings.ToLower(strings.Join(strings.Fields(s), " ")) }

func (s *BudgetService) GetBudget(ctx context.Context, req *connect.Request[budgetv1.GetBudgetRequest]) (*connect.Response[budgetv1.GetBudgetResponse], error) {
	tree, err := s.Budget.Tree(ctx)
	if err != nil {
		return nil, connect.NewError(connect.CodeUnavailable, errors.New("the budget (GOrdian) is not reachable right now"))
	}

	// The claim being edited does not count against its own budget lines.
	var exclude int64
	if ref := req.Msg.Exclude; ref != nil {
		if summary, err := s.Store.Get(ctx, callerFrom(ctx).viewer, kindFromProto[ref.Kind], ref.Number); err == nil {
			exclude = summary.ID
		}
	}
	year := time.Now().In(stockholm).Year()
	if y := int(req.Msg.Year); y >= 2000 && y <= year+1 {
		year = y
	}
	usage, err := s.Store.Queries.BudgetUsage(ctx, db.BudgetUsageParams{
		FromDate:       pgtype.Date{Time: time.Date(year, 1, 1, 0, 0, 0, 0, time.UTC), Valid: true},
		ToDate:         pgtype.Date{Time: time.Date(year+1, 1, 1, 0, 0, 0, 0, time.UTC), Valid: true},
		ExcludeClaimID: exclude,
	})
	if err != nil {
		return nil, err
	}
	used := map[[3]string]db.BudgetUsageRow{}
	for _, u := range usage {
		used[[3]string{u.CostCentre, u.SecondaryCostCentre, u.BudgetLine}] = u
	}

	res := &budgetv1.GetBudgetResponse{Year: int32(year)}
	for _, cc := range tree {
		pcc := &budgetv1.CostCentre{Id: int32(cc.ID), Name: cc.Name, Type: cc.Type}
		for _, scc := range cc.Secondary {
			pscc := &budgetv1.SecondaryCostCentre{Id: int32(scc.ID), Name: scc.Name}
			for _, l := range scc.Lines {
				accounts := make([]int32, len(l.Accounts))
				for i, a := range l.Accounts {
					accounts[i] = int32(a)
				}
				u := used[[3]string{normaliseName(cc.Name), normaliseName(scc.Name), normaliseName(l.Name)}]
				// Cashflow 3's _is_blown: lines without an expense budget can't be.
				blown := l.ExpenseOre > 0 && u.UploadedOre > l.ExpenseOre
				pcc.ContainsBlown = pcc.ContainsBlown || blown
				pscc.Lines = append(pscc.Lines, &budgetv1.BudgetLine{
					Id: int32(l.ID), Name: l.Name, Accounts: accounts, ExpenseOre: l.ExpenseOre, IncomeOre: l.IncomeOre,
					Comment: l.Comment, UsedOre: u.UploadedOre, AttestedOre: u.AttestedOre, PaidOre: u.PaidOre, Blown: blown,
				})
			}
			pcc.Secondary = append(pcc.Secondary, pscc)
		}
		res.CostCentres = append(res.CostCentres, pcc)
	}
	return connect.NewResponse(res), nil
}
