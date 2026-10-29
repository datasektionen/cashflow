package rpc

import (
	"context"

	"connectrpc.com/connect"

	userv1 "github.com/datasektionen/cashflow/server/gen/cashflow/user/v1"
	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

type UserService struct {
	Queries *db.Queries
}

func (s *UserService) GetMe(ctx context.Context, _ *connect.Request[userv1.GetMeRequest]) (*connect.Response[userv1.GetMeResponse], error) {
	c := callerFrom(ctx)

	// The frontend calls GetMe on load, which is when a new SSO user gets a row.
	u, err := s.Queries.UpsertUser(ctx, db.UpsertUserParams{
		Username: c.user.Username,
		Name:     c.user.Name,
		Email:    c.user.Email,
	})
	if err != nil {
		return nil, err
	}
	costCentres, err := s.Queries.ListCostCentres(ctx)
	if err != nil {
		return nil, err
	}

	p := c.perms
	return connect.NewResponse(&userv1.GetMeResponse{
		User: &userv1.User{
			Username:       u.Username,
			Name:           u.Name,
			Email:          u.Email,
			BankAccount:    u.BankAccount,
			ClearingNumber: u.ClearingNumber,
			BankName:       u.BankName,
		},
		Capabilities: &userv1.Capabilities{
			ViewAll:               p.MayViewAll(),
			ViewAllPayments:       p.MayViewAllPayments(),
			ViewCostCentres:       perm.Filter(costCentres, p.MayViewCostCentre),
			AttestAll:             p.MayAttestAll(),
			AttestCostCentres:     perm.Filter(costCentres, p.MayAttest),
			Unattest:              p.MayUnattest(),
			Confirm:               p.MayConfirm(),
			AccountingAll:         p.MayAccountAll(),
			AccountingCostCentres: perm.Filter(costCentres, p.MayAccount),
			Pay:                   p.MayPay(),
			Delete:                p.MayDelete(),
			EditInvoice:           p.MayEditInvoice(),
			ModerateComments:      p.MayModerateComments(),
			ManageFortnox:         p.MayManageFortnox(),
			Firmatecknare:         p.MayFirmatecknare(),
			ViewAccount:           p.MayViewAccount(),
		},
	}), nil
}
