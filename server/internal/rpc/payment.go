package rpc

import (
	"context"
	"fmt"
	"time"

	"connectrpc.com/connect"

	claimv1 "github.com/datasektionen/cashflow/server/gen/cashflow/claim/v1"
	paymentv1 "github.com/datasektionen/cashflow/server/gen/cashflow/payment/v1"
	"github.com/datasektionen/cashflow/server/internal/claims"
)

type PaymentService struct {
	Store *claims.Store
}

func (s *PaymentService) ListPendingPayouts(ctx context.Context, _ *connect.Request[paymentv1.ListPendingPayoutsRequest]) (*connect.Response[paymentv1.ListPendingPayoutsResponse], error) {
	pending, err := s.Store.PendingPayouts(ctx, callerFrom(ctx).viewer)
	if err != nil {
		return nil, claimError(err)
	}
	res := &paymentv1.ListPendingPayoutsResponse{}
	for _, p := range pending {
		payout := &paymentv1.PendingPayout{
			Receiver: &claimv1.Person{Username: p.Receiver.Username, Name: p.Receiver.Name},
			Bank:     toProtoBank(p.Bank),
			TotalOre: p.TotalOre,
		}
		for _, e := range p.Expenses {
			payout.Expenses = append(payout.Expenses, toProtoSummary(e))
		}
		res.Payouts = append(res.Payouts, payout)
	}
	return connect.NewResponse(res), nil
}

func (s *PaymentService) CreatePayout(ctx context.Context, req *connect.Request[paymentv1.CreatePayoutRequest]) (*connect.Response[paymentv1.CreatePayoutResponse], error) {
	viewer := callerFrom(ctx).viewer
	id, err := s.Store.CreatePayout(ctx, viewer, req.Msg.ExpenseNumbers)
	if err != nil {
		return nil, claimError(err)
	}
	payments, _, err := s.Store.ListPayments(ctx, viewer, claims.PaymentTag(id), 1, claims.MaxPageSize)
	if err != nil {
		return nil, err
	}
	var payment *claims.Payment
	for i := range payments {
		if payments[i].ID == id {
			payment = &payments[i]
		}
	}
	if payment == nil {
		return nil, fmt.Errorf("payout %d not found after creating it", id)
	}
	receiver, err := s.Store.Queries.GetUser(ctx, payment.Receiver.Username)
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&paymentv1.CreatePayoutResponse{
		Payment: toProtoPayment(*payment),
		Bank:    toProtoBank(claims.BankDetails{ClearingNumber: receiver.SortingNumber, Account: receiver.BankAccount, BankName: receiver.BankName}),
	}), nil
}

func (s *PaymentService) ListPayments(ctx context.Context, req *connect.Request[paymentv1.ListPaymentsRequest]) (*connect.Response[paymentv1.ListPaymentsResponse], error) {
	payments, total, err := s.Store.ListPayments(ctx, callerFrom(ctx).viewer, req.Msg.Query, int(req.Msg.Page), int(req.Msg.PageSize))
	if err != nil {
		return nil, claimError(err)
	}
	res := &paymentv1.ListPaymentsResponse{Total: int32(total)}
	for _, p := range payments {
		res.Payments = append(res.Payments, toProtoPayment(p))
	}
	return connect.NewResponse(res), nil
}

func toProtoPayment(p claims.Payment) *paymentv1.Payment {
	return &paymentv1.Payment{
		Id:             p.ID,
		Tag:            p.Tag,
		Date:           p.Date.Format(time.DateOnly),
		Payer:          &claimv1.Person{Username: p.Payer.Username, Name: p.Payer.Name},
		Receiver:       &claimv1.Person{Username: p.Receiver.Username, Name: p.Receiver.Name},
		TotalOre:       p.TotalOre,
		ExpenseNumbers: p.Expenses,
	}
}

func toProtoBank(b claims.BankDetails) *paymentv1.BankDetails {
	return &paymentv1.BankDetails{ClearingNumber: b.ClearingNumber, Account: b.Account, BankName: b.BankName}
}
