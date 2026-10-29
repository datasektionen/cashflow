package rpc

import (
	"context"
	"errors"
	"log/slog"
	"strings"
	"unicode"
	"unicode/utf8"

	"connectrpc.com/connect"
	auth "github.com/datasektionen/GO-auth-yourself"
	"github.com/jackc/pgx/v5"

	userv1 "github.com/datasektionen/cashflow/server/gen/cashflow/user/v1"
	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/perm"
	"github.com/datasektionen/cashflow/server/internal/rfinger"
)

type UserService struct {
	Queries  *db.Queries
	Pictures *rfinger.Client
}

func (s *UserService) GetMe(ctx context.Context, _ *connect.Request[userv1.GetMeRequest]) (*connect.Response[userv1.GetMeResponse], error) {
	c := callerFrom(ctx)

	// The frontend calls GetMe on load, which is when a new SSO user gets a row.
	if err := s.ensureUser(ctx, c.user); err != nil {
		return nil, err
	}
	u, err := s.Queries.GetUser(ctx, c.user.Username)
	if err != nil {
		return nil, err
	}
	costCentres, err := s.Queries.ListCostCentres(ctx)
	if err != nil {
		return nil, err
	}

	p := c.perms
	return connect.NewResponse(&userv1.GetMeResponse{
		User: toProtoUser(u),
		Capabilities: &userv1.Capabilities{
			ViewAll:               p.MayViewAll(),
			ViewAllPayments:       p.MayViewAllPayments(),
			ViewCostCentres:       perm.Filter(costCentres, p.MayViewCostCentre),
			AttestAll:             p.MayAttestAll(),
			AttestAny:             p.MayAttestSome(),
			AttestCostCentres:     perm.Filter(costCentres, p.MayAttest),
			Unattest:              p.MayUnattest(),
			Confirm:               p.MayConfirm(),
			AccountingAll:         p.MayAccountAll(),
			AccountingAny:         p.MayAccountSome(),
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

// ensureUser creates the Django user and profile rows on a first login. Two
// first requests can race: the loser inserts nothing and, not seeing the
// winner's uncommitted row, finds no user, so it tries once more.
func (s *UserService) ensureUser(ctx context.Context, user auth.User) error {
	first, last, _ := strings.Cut(user.Name, " ")
	params := db.UpsertUserParams{Username: user.Username, FirstName: first, LastName: last, Email: user.Email}
	for attempt := 0; ; attempt++ {
		_, err := s.Queries.UpsertUser(ctx, params)
		if errors.Is(err, pgx.ErrNoRows) && attempt == 0 {
			continue
		}
		return err
	}
}

func (s *UserService) UpdateBankDetails(ctx context.Context, req *connect.Request[userv1.UpdateBankDetailsRequest]) (*connect.Response[userv1.UpdateBankDetailsResponse], error) {
	details, err := parseBankDetails(req.Msg)
	if err != nil {
		return nil, err
	}
	details.Username = callerFrom(ctx).user.Username

	if err := s.Queries.UpdateBankDetails(ctx, details); err != nil {
		return nil, err
	}
	u, err := s.Queries.GetUser(ctx, details.Username)
	if err != nil {
		return nil, err
	}
	return connect.NewResponse(&userv1.UpdateBankDetailsResponse{User: toProtoUser(u)}), nil
}

// parseBankDetails normalises and validates bank details. Clearing number and
// account number are set together or both cleared; spaces, dots and dashes
// are dropped so "8327-9" and "8327 9" store the same.
func parseBankDetails(msg *userv1.UpdateBankDetailsRequest) (db.UpdateBankDetailsParams, error) {
	clearing := digitsOnly(msg.ClearingNumber)
	account := digitsOnly(msg.BankAccount)
	bankName := strings.TrimSpace(msg.BankName)

	var v violations
	switch {
	case !isDigits(clearing):
		v.add("clearing_number", "clearing_number.digits")
	case clearing == "" && account != "":
		v.add("clearing_number", "clearing_number.required")
	case clearing != "" && (len(clearing) < 4 || len(clearing) > 5):
		v.add("clearing_number", "clearing_number.length")
	}
	switch {
	case !isDigits(account):
		v.add("bank_account", "bank_account.digits")
	case account == "" && clearing != "":
		v.add("bank_account", "bank_account.required")
	case len(account) > 13:
		v.add("bank_account", "bank_account.length")
	}
	if utf8.RuneCountInString(bankName) > 30 {
		v.add("bank_name", "bank_name.length")
	}

	return db.UpdateBankDetailsParams{ClearingNumber: clearing, BankAccount: account, BankName: bankName}, v.err()
}

func digitsOnly(s string) string {
	return strings.Map(func(r rune) rune {
		if unicode.IsSpace(r) || r == '-' || r == '.' {
			return -1
		}
		return r
	}, s)
}

func isDigits(s string) bool {
	for _, r := range s {
		if r < '0' || r > '9' {
			return false
		}
	}
	return true
}

func toProtoUser(u db.GetUserRow) *userv1.User {
	return &userv1.User{
		Username:       u.Username,
		Name:           strings.TrimSpace(u.FirstName + " " + u.LastName),
		Email:          u.Email,
		BankAccount:    u.BankAccount,
		ClearingNumber: u.SortingNumber,
		BankName:       u.BankName,
	}
}

// GetProfilePictures asks rfinger, at most 100 users at a time. A failing
// rfinger is not an error for the page: everyone shows their initials.
func (s *UserService) GetProfilePictures(ctx context.Context, req *connect.Request[userv1.GetProfilePicturesRequest]) (*connect.Response[userv1.GetProfilePicturesResponse], error) {
	usernames := req.Msg.Usernames
	if len(usernames) > 100 {
		return nil, connect.NewError(connect.CodeInvalidArgument, errors.New("at most 100 usernames"))
	}
	urls, err := s.Pictures.Pictures(ctx, usernames)
	if err != nil {
		slog.Warn("profile pictures unavailable", "error", err)
		urls = map[string]string{}
	}
	return connect.NewResponse(&userv1.GetProfilePicturesResponse{Urls: urls}), nil
}
