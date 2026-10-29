package rpc

import (
	"context"
	"errors"
	"fmt"
	"path"
	"time"

	"connectrpc.com/connect"
	"github.com/jackc/pgx/v5/pgtype"
	"google.golang.org/protobuf/types/known/timestamppb"

	claimv1 "github.com/datasektionen/cashflow/server/gen/cashflow/claim/v1"
	"github.com/datasektionen/cashflow/server/internal/claims"
	"github.com/datasektionen/cashflow/server/internal/storage"
)

type ClaimService struct {
	Store *claims.Store
}

func (s *ClaimService) ListClaims(ctx context.Context, req *connect.Request[claimv1.ListClaimsRequest]) (*connect.Response[claimv1.ListClaimsResponse], error) {
	m := req.Msg
	f := claims.Filter{
		Mine:       m.Mine,
		Queue:      queueFromProto[m.Queue],
		Kind:       kindFromProto[m.Kind],
		Query:      m.Query,
		CostCentre: m.CostCentre,
		Sort:       sortFromProto[m.Sort],
		Descending: m.Descending,
		Page:       int(m.Page),
		PageSize:   int(m.PageSize),
	}
	list, total, err := s.Store.List(ctx, callerFrom(ctx).viewer, f)
	if err != nil {
		return nil, claimError(err)
	}
	res := &claimv1.ListClaimsResponse{Total: int32(total)}
	for _, c := range list {
		res.Claims = append(res.Claims, toProtoSummary(c))
	}
	return connect.NewResponse(res), nil
}

func (s *ClaimService) GetClaim(ctx context.Context, req *connect.Request[claimv1.GetClaimRequest]) (*connect.Response[claimv1.GetClaimResponse], error) {
	kind := kindFromProto[req.Msg.Kind]
	if kind == "" || req.Msg.Number <= 0 {
		return nil, connect.NewError(connect.CodeInvalidArgument, errors.New("kind and number are required"))
	}
	summary, err := s.Store.Get(ctx, callerFrom(ctx).viewer, kind, req.Msg.Number)
	if err != nil {
		return nil, claimError(err)
	}
	claim, err := s.details(ctx, summary)
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&claimv1.GetClaimResponse{Claim: claim}), nil
}

func (s *ClaimService) details(ctx context.Context, summary claims.Summary) (*claimv1.Claim, error) {
	q := s.Store.Queries
	claim := &claimv1.Claim{Summary: toProtoSummary(summary)}

	parts, err := q.ListClaimParts(ctx, summary.ID)
	if err != nil {
		return nil, fmt.Errorf("parts: %w", err)
	}
	for _, p := range parts {
		claim.Parts = append(claim.Parts, &claimv1.Part{
			Id:                  p.ID,
			CostCentre:          p.CostCentre,
			SecondaryCostCentre: p.SecondaryCostCentre,
			BudgetLine:          p.BudgetLine,
			AmountOre:           p.AmountOre,
			AttestedBy:          person(p.AttestedByUsername, p.AttestedByName),
			AttestedAt:          isoDate(p.AttestDate),
		})
	}

	files, err := q.ListClaimFiles(ctx, summary.ID)
	if err != nil {
		return nil, fmt.Errorf("files: %w", err)
	}
	for _, f := range files {
		claim.Files = append(claim.Files, &claimv1.File{
			Id:          f.ID,
			Name:        path.Base(f.File),
			ContentType: storage.ContentType(f.File),
			Url:         fmt.Sprintf("/files/%d", f.ID),
		})
	}

	comments, err := q.ListClaimComments(ctx, summary.ID)
	if err != nil {
		return nil, fmt.Errorf("comments: %w", err)
	}
	for _, c := range comments {
		claim.Comments = append(claim.Comments, &claimv1.Comment{
			Author:    person(c.AuthorUsername, c.AuthorName),
			Body:      c.Content,
			CreatedAt: timestamppb.New(c.Date.Time),
		})
	}

	switch summary.Kind {
	case claims.Expense:
		e, err := q.GetExpenseDetails(ctx, summary.ID)
		if err != nil {
			return nil, fmt.Errorf("expense: %w", err)
		}
		claim.ConfirmedBy = person(e.ConfirmedByUsername, e.ConfirmedByName)
		claim.ConfirmedAt = isoDate(e.ConfirmedAt)
		if e.PaymentID.Valid {
			claim.Payment = &claimv1.Payment{
				Id:    e.PaymentID.Int64,
				Tag:   claims.PaymentTag(e.PaymentID.Int64),
				Payer: person(e.PayerUsername, e.PayerName),
				Date:  isoDate(e.PaymentDate),
			}
		}
	case claims.Invoice:
		i, err := q.GetInvoiceDetails(ctx, summary.ID)
		if err != nil {
			return nil, fmt.Errorf("invoice: %w", err)
		}
		claim.InvoiceNumber = i.InvoiceNumber
		claim.DueDate = isoDate(i.DueDate)
		claim.PaidBy = person(i.PaidByUsername, i.PaidByName)
		claim.PaidAt = isoDate(i.PaidAt)
	}
	return claim, nil
}

func (s *ClaimService) GetQueueCounts(ctx context.Context, _ *connect.Request[claimv1.GetQueueCountsRequest]) (*connect.Response[claimv1.GetQueueCountsResponse], error) {
	viewer := callerFrom(ctx).viewer
	res := &claimv1.GetQueueCountsResponse{}
	for _, q := range claims.Queues {
		if !viewer.MaySeeQueue(q) {
			continue
		}
		n, err := s.Store.Count(ctx, viewer, q)
		if err != nil {
			return nil, err
		}
		res.Counts = append(res.Counts, &claimv1.QueueCount{Queue: queueToProto[q], Count: int32(n)})
	}
	return connect.NewResponse(res), nil
}

func (s *ClaimService) GetOverview(ctx context.Context, _ *connect.Request[claimv1.GetOverviewRequest]) (*connect.Response[claimv1.GetOverviewResponse], error) {
	o, err := s.Store.Queries.GetOverview(ctx, callerFrom(ctx).user.Username)
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&claimv1.GetOverviewResponse{
		AwaitingAttestOre:  o.AwaitingAttestOre,
		AwaitingPaymentOre: o.AwaitingPaymentOre,
		PaidThisYearOre:    o.PaidThisYearOre,
	}), nil
}

func claimError(err error) error {
	switch {
	case errors.Is(err, claims.ErrNotFound):
		return connect.NewError(connect.CodeNotFound, err)
	case errors.Is(err, claims.ErrForbiddenQueue):
		return connect.NewError(connect.CodePermissionDenied, err)
	}
	return err
}

func toProtoSummary(c claims.Summary) *claimv1.ClaimSummary {
	date := ""
	if c.Date != nil {
		date = c.Date.Format(time.DateOnly)
	}
	return &claimv1.ClaimSummary{
		Kind:        kindToProto[c.Kind],
		Number:      c.Number,
		Description: c.Description,
		Owner:       &claimv1.Person{Username: c.Owner.Username, Name: c.Owner.Name},
		AmountOre:   c.AmountOre,
		Date:        date,
		CreatedDate: c.CreatedDate.Format(time.DateOnly),
		CostCentres: c.CostCentres,
		Status: &claimv1.Status{
			// claims.Stage numbers match the proto enum.
			Stage:        claimv1.Stage(c.Stage()),
			Attested:     c.Attested,
			Confirmed:    c.Confirmed,
			Paid:         c.Paid,
			Verification: c.Verification,
			Flagged:      c.Flagged,
		},
	}
}

// person returns nil for "nobody", so optional people are absent in the API.
func person(username, name string) *claimv1.Person {
	if username == "" {
		return nil
	}
	return &claimv1.Person{Username: username, Name: name}
}

func isoDate(d pgtype.Date) string {
	if !d.Valid {
		return ""
	}
	return d.Time.Format(time.DateOnly)
}

var (
	kindFromProto = map[claimv1.ClaimKind]claims.Kind{
		claimv1.ClaimKind_CLAIM_KIND_EXPENSE: claims.Expense,
		claimv1.ClaimKind_CLAIM_KIND_INVOICE: claims.Invoice,
	}
	kindToProto    = invert(kindFromProto)
	queueFromProto = map[claimv1.Queue]claims.Queue{
		claimv1.Queue_QUEUE_ATTEST:  claims.QueueAttest,
		claimv1.Queue_QUEUE_CONFIRM: claims.QueueConfirm,
		claimv1.Queue_QUEUE_ACCOUNT: claims.QueueAccount,
		claimv1.Queue_QUEUE_PAY:     claims.QueuePay,
	}
	queueToProto  = invert(queueFromProto)
	sortFromProto = map[claimv1.SortField]claims.Sort{
		claimv1.SortField_SORT_FIELD_DATE:        claims.SortDate,
		claimv1.SortField_SORT_FIELD_AMOUNT:      claims.SortAmount,
		claimv1.SortField_SORT_FIELD_DESCRIPTION: claims.SortDescription,
		claimv1.SortField_SORT_FIELD_OWNER:       claims.SortOwner,
		claimv1.SortField_SORT_FIELD_CREATED:     claims.SortCreated,
	}
)

func invert[K, V comparable](m map[K]V) map[V]K {
	out := make(map[V]K, len(m))
	for k, v := range m {
		out[v] = k
	}
	return out
}
