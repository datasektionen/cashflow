package rpc

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"connectrpc.com/connect"
	"google.golang.org/protobuf/types/known/timestamppb"

	accountingv1 "github.com/datasektionen/cashflow/server/gen/cashflow/accounting/v1"
	claimv1 "github.com/datasektionen/cashflow/server/gen/cashflow/claim/v1"
	"github.com/datasektionen/cashflow/server/internal/budget"
	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/fortnox"
)

type AccountingService struct {
	Store   *claims.Store
	Claims  *ClaimService
	Fortnox *fortnox.Client // nil when Fortnox is off
	Budget  *budget.Client
}

var errNoFortnox = errors.New("fortnox is not enabled on this server")

// mayUseFortnox: Cashflow 3's AccountingPermission.
func mayUseFortnox(c caller) bool { return c.perms.MayAccountSome() || c.perms.MayViewAll() }

func (s *AccountingService) GetFortnoxStatus(ctx context.Context, _ *connect.Request[accountingv1.GetFortnoxStatusRequest]) (*connect.Response[accountingv1.GetFortnoxStatusResponse], error) {
	c := callerFrom(ctx)
	if !c.perms.MayManageFortnox() && !c.perms.MayViewAll() {
		return nil, connect.NewError(connect.CodePermissionDenied, errors.New("only those who manage Fortnox may see its status"))
	}
	res := &accountingv1.GetFortnoxStatusResponse{Enabled: s.Fortnox.Enabled()}
	if !res.Enabled {
		return connect.NewResponse(res), nil
	}
	conn, err := s.Fortnox.Connection(ctx)
	if err != nil {
		return nil, err
	}
	if conn != nil {
		res.Connected = true
		res.ConnectedBy = &claimv1.Person{Username: conn.Username, Name: conn.Name}
		res.ConnectedAt = timestamppb.New(conn.ConnectedAt)
	}
	return connect.NewResponse(res), nil
}

func (s *AccountingService) DisconnectFortnox(ctx context.Context, _ *connect.Request[accountingv1.DisconnectFortnoxRequest]) (*connect.Response[accountingv1.DisconnectFortnoxResponse], error) {
	c := callerFrom(ctx)
	if !c.perms.MayManageFortnox() {
		return nil, connect.NewError(connect.CodePermissionDenied, errors.New("only those who manage Fortnox may disconnect it"))
	}
	if !s.Fortnox.Enabled() {
		return nil, connect.NewError(connect.CodeFailedPrecondition, errNoFortnox)
	}
	if err := s.Fortnox.Disconnect(ctx); err != nil {
		return nil, err
	}
	slog.Warn("fortnox disconnected", "by", c.user.Username)
	return connect.NewResponse(&accountingv1.DisconnectFortnoxResponse{}), nil
}

// fortnoxFor checks the caller may read Fortnox's lists and that it is on.
func (s *AccountingService) fortnoxFor(ctx context.Context) error {
	if !mayUseFortnox(callerFrom(ctx)) {
		return connect.NewError(connect.CodePermissionDenied, errors.New("only accountants may read Fortnox"))
	}
	if !s.Fortnox.Enabled() {
		return claimError(claims.ErrFortnoxDisabled)
	}
	return nil
}

func (s *AccountingService) ListFortnoxAccounts(ctx context.Context, _ *connect.Request[accountingv1.ListFortnoxAccountsRequest]) (*connect.Response[accountingv1.ListFortnoxAccountsResponse], error) {
	if err := s.fortnoxFor(ctx); err != nil {
		return nil, err
	}
	accounts, err := s.Fortnox.Accounts(ctx)
	if err != nil {
		return nil, fortnoxError(err)
	}
	res := &accountingv1.ListFortnoxAccountsResponse{}
	for _, a := range accounts {
		res.Accounts = append(res.Accounts, &accountingv1.FortnoxAccount{Number: int32(a.Number), Description: a.Description})
	}
	return connect.NewResponse(res), nil
}

func (s *AccountingService) ListFortnoxCostCentres(ctx context.Context, _ *connect.Request[accountingv1.ListFortnoxCostCentresRequest]) (*connect.Response[accountingv1.ListFortnoxCostCentresResponse], error) {
	if err := s.fortnoxFor(ctx); err != nil {
		return nil, err
	}
	ccs, err := s.Fortnox.CostCentres(ctx)
	if err != nil {
		return nil, fortnoxError(err)
	}
	res := &accountingv1.ListFortnoxCostCentresResponse{}
	for _, cc := range ccs {
		res.CostCentres = append(res.CostCentres, &accountingv1.FortnoxCostCentre{Code: cc.Code, Description: cc.Description})
	}
	return connect.NewResponse(res), nil
}

func (s *AccountingService) ListVoucherSeries(ctx context.Context, _ *connect.Request[accountingv1.ListVoucherSeriesRequest]) (*connect.Response[accountingv1.ListVoucherSeriesResponse], error) {
	res := &accountingv1.ListVoucherSeriesResponse{}
	known := map[string]bool{}
	// Fortnox's series come first when it is reachable; the list still works
	// from accounted claims when it is not.
	if s.Fortnox.Enabled() && mayUseFortnox(callerFrom(ctx)) {
		series, err := s.Fortnox.VoucherSeries(ctx)
		if err != nil && !errors.Is(err, fortnox.ErrNotConnected) {
			slog.Warn("listing fortnox voucher series failed", "error", err)
		}
		for _, vs := range series {
			// Cashflow's voucher numbers are one letter and digits.
			if len(vs.Code) == 1 && vs.Code[0] >= 'A' && vs.Code[0] <= 'Z' && !known[vs.Code] {
				known[vs.Code] = true
				res.Series = append(res.Series, &accountingv1.VoucherSeries{Code: vs.Code, Description: vs.Description, InFortnox: true})
			}
		}
	}
	codes, err := s.Store.Queries.ListVerificationSeries(ctx)
	if err != nil {
		return nil, err
	}
	for _, code := range codes {
		if !known[code] {
			res.Series = append(res.Series, &accountingv1.VoucherSeries{Code: code})
		}
	}
	return connect.NewResponse(res), nil
}

func (s *AccountingService) GetVoucherDraft(ctx context.Context, req *connect.Request[accountingv1.GetVoucherDraftRequest]) (*connect.Response[accountingv1.GetVoucherDraftResponse], error) {
	c := callerFrom(ctx)
	kind, number, err := ref(req.Msg.Claim)
	if err != nil {
		return nil, err
	}
	if !mayUseFortnox(c) {
		return nil, connect.NewError(connect.CodePermissionDenied, errors.New("only accountants may draft vouchers"))
	}
	summary, err := s.Store.Get(ctx, c.viewer, kind, number)
	if err != nil {
		return nil, claimError(err)
	}
	q := s.Store.Queries
	details, err := q.GetVoucherDetails(ctx, summary.ID)
	if err != nil {
		return nil, err
	}
	rows, err := q.ListClaimParts(ctx, summary.ID)
	if err != nil {
		return nil, err
	}
	parts := make([]claims.DraftPart, len(rows))
	for i, p := range rows {
		parts[i] = claims.DraftPart{CostCentre: p.CostCentre, SecondaryCostCentre: p.SecondaryCostCentre, BudgetLine: p.BudgetLine, AmountOre: p.AmountOre}
	}

	// Suggestions are best effort: without GOrdian or Fortnox the rows just
	// start without an account or cost centre.
	tree, err := s.Budget.Tree(ctx)
	if err != nil {
		slog.Warn("voucher draft without budget accounts", "error", err)
	}
	available := false
	var costCentres []fortnox.CostCentre
	if s.Fortnox.Enabled() {
		costCentres, err = s.Fortnox.CostCentres(ctx)
		available = err == nil
		if err != nil && !errors.Is(err, fortnox.ErrNotConnected) {
			slog.Warn("voucher draft without fortnox cost centres", "error", err)
		}
	}
	date := ""
	if details.Date.Valid {
		date = details.Date.Time.Format(time.DateOnly)
	}
	draft := claims.BuildDraft(kind, number, summary.Description, date, parts, tree, costCentres)

	res := &accountingv1.GetVoucherDraftResponse{
		Series: draft.Series, Description: draft.Description, TransactionDate: draft.TransactionDate,
		TotalOre: draft.TotalOre, FortnoxAvailable: available,
	}
	for _, r := range draft.Rows {
		res.Rows = append(res.Rows, &accountingv1.DraftRow{
			Row:   &accountingv1.VoucherRow{Account: int32(r.Account), CostCentre: r.CostCentre, DebitOre: r.DebitOre, CreditOre: r.CreditOre},
			Label: r.Label, Balancing: r.Balancing,
		})
	}
	return connect.NewResponse(res), nil
}

func (s *AccountingService) AccountClaim(ctx context.Context, req *connect.Request[accountingv1.AccountClaimRequest]) (*connect.Response[accountingv1.AccountClaimResponse], error) {
	kind, number, err := ref(req.Msg.Claim)
	if err != nil {
		return nil, err
	}
	in := claims.AccountingInput{VoucherNumber: req.Msg.GetVoucherNumber()}
	for _, r := range req.Msg.GetRows().GetRows() {
		in.Rows = append(in.Rows, fortnox.VoucherRow{
			Account: int(r.Account), CostCentre: r.CostCentre, Debit: fortnox.Kronor(r.DebitOre), Credit: fortnox.Kronor(r.CreditOre),
		})
	}
	if in.VoucherNumber == "" && len(in.Rows) == 0 {
		var v violations
		v.add("method", "method.required")
		return nil, v.err()
	}
	voucher, err := s.Store.Account(ctx, callerFrom(ctx).viewer, kind, number, in, s.Fortnox)
	if err != nil {
		return nil, inputError(err)
	}
	claim, err := s.Claims.load(ctx, kind, number)
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&accountingv1.AccountClaimResponse{Claim: claim, VoucherNumber: voucher}), nil
}

// fortnoxError reports Fortnox being disconnected or refusing as problems.
func fortnoxError(err error) error {
	if errors.Is(err, fortnox.ErrNotConnected) {
		return claimError(claims.ErrFortnoxNotConnected)
	}
	return connect.NewError(connect.CodeUnavailable, fmt.Errorf("fortnox: %w", err))
}
