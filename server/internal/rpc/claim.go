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
	commonv1 "github.com/datasektionen/cashflow/server/gen/cashflow/common/v1"
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
	claim, err := s.load(ctx, kind, req.Msg.Number)
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&claimv1.GetClaimResponse{Claim: claim}), nil
}

// load returns a claim in full, with what the caller may do with it.
func (s *ClaimService) load(ctx context.Context, kind claims.Kind, number int64) (*claimv1.Claim, error) {
	viewer := callerFrom(ctx).viewer
	summary, err := s.Store.Get(ctx, viewer, kind, number)
	if err != nil {
		return nil, claimError(err)
	}
	q := s.Store.Queries
	claim := &claimv1.Claim{Summary: toProtoSummary(summary)}

	state, err := s.Store.State(ctx, viewer, summary)
	if err != nil {
		return nil, fmt.Errorf("state: %w", err)
	}
	a := viewer.Actions(state)
	claim.Actions = &claimv1.Actions{
		AttestPartIds: a.Attest, UnattestPartIds: a.Unattest,
		Confirm: a.Confirm, Unconfirm: a.Unconfirm, Flag: a.Flag, Unflag: a.Unflag,
		Pay: a.PayInvoice, Delete: a.Delete, Edit: a.Edit,
	}

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
	if problem, ok := claims.IsProblem(err); ok {
		code := connect.CodeFailedPrecondition
		if problem.Forbidden {
			code = connect.CodePermissionDenied
		}
		cerr := connect.NewError(code, err)
		if detail, err := connect.NewErrorDetail(&commonv1.Problem{Code: problem.Code}); err == nil {
			cerr.AddDetail(detail)
		}
		return cerr
	}
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

// ref validates a claim reference from a request.
func ref(r *claimv1.ClaimRef) (claims.Kind, int64, error) {
	kind := kindFromProto[r.GetKind()]
	if kind == "" || r.GetNumber() <= 0 {
		return "", 0, connect.NewError(connect.CodeInvalidArgument, errors.New("a claim kind and number are required"))
	}
	return kind, r.GetNumber(), nil
}

// after runs a workflow change and returns the claim as it is afterwards.
func (s *ClaimService) after(ctx context.Context, kind claims.Kind, number int64, change func(claims.Viewer) error) (*claimv1.Claim, error) {
	if err := change(callerFrom(ctx).viewer); err != nil {
		return nil, claimError(err)
	}
	return s.load(ctx, kind, number)
}

func (s *ClaimService) AddComment(ctx context.Context, req *connect.Request[claimv1.AddCommentRequest]) (*connect.Response[claimv1.AddCommentResponse], error) {
	kind, number, err := ref(req.Msg.Claim)
	if err != nil {
		return nil, err
	}
	claim, err := s.after(ctx, kind, number, func(v claims.Viewer) error {
		return s.Store.AddComment(ctx, v, kind, number, req.Msg.Body)
	})
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&claimv1.AddCommentResponse{Claim: claim}), nil
}

func (s *ClaimService) SetPartAttested(ctx context.Context, req *connect.Request[claimv1.SetPartAttestedRequest]) (*connect.Response[claimv1.SetPartAttestedResponse], error) {
	kind, number, err := ref(req.Msg.Claim)
	if err != nil {
		return nil, err
	}
	claim, err := s.after(ctx, kind, number, func(v claims.Viewer) error {
		return s.Store.SetAttested(ctx, v, kind, number, req.Msg.PartId, req.Msg.Attested)
	})
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&claimv1.SetPartAttestedResponse{Claim: claim}), nil
}

func (s *ClaimService) SetConfirmed(ctx context.Context, req *connect.Request[claimv1.SetConfirmedRequest]) (*connect.Response[claimv1.SetConfirmedResponse], error) {
	claim, err := s.after(ctx, claims.Expense, req.Msg.Number, func(v claims.Viewer) error {
		return s.Store.SetConfirmed(ctx, v, req.Msg.Number, req.Msg.Confirmed)
	})
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&claimv1.SetConfirmedResponse{Claim: claim}), nil
}

func (s *ClaimService) SetFlagged(ctx context.Context, req *connect.Request[claimv1.SetFlaggedRequest]) (*connect.Response[claimv1.SetFlaggedResponse], error) {
	claim, err := s.after(ctx, claims.Expense, req.Msg.Number, func(v claims.Viewer) error {
		return s.Store.SetFlagged(ctx, v, req.Msg.Number, req.Msg.Flagged)
	})
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&claimv1.SetFlaggedResponse{Claim: claim}), nil
}

func (s *ClaimService) PayInvoice(ctx context.Context, req *connect.Request[claimv1.PayInvoiceRequest]) (*connect.Response[claimv1.PayInvoiceResponse], error) {
	claim, err := s.after(ctx, claims.Invoice, req.Msg.Number, func(v claims.Viewer) error {
		return s.Store.PayInvoice(ctx, v, req.Msg.Number)
	})
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&claimv1.PayInvoiceResponse{Claim: claim}), nil
}

func (s *ClaimService) DeleteClaim(ctx context.Context, req *connect.Request[claimv1.DeleteClaimRequest]) (*connect.Response[claimv1.DeleteClaimResponse], error) {
	kind, number, err := ref(req.Msg.Claim)
	if err != nil {
		return nil, err
	}
	if err := s.Store.Delete(ctx, callerFrom(ctx).viewer, kind, number); err != nil {
		return nil, claimError(err)
	}
	return connect.NewResponse(&claimv1.DeleteClaimResponse{}), nil
}
