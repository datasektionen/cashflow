package rpc

import (
	"errors"
	"slices"
	"testing"

	"connectrpc.com/connect"

	commonv1 "github.com/datasektionen/cashflow/server/gen/cashflow/common/v1"
	userv1 "github.com/datasektionen/cashflow/server/gen/cashflow/user/v1"
)

func violationCodes(t *testing.T, err error) []string {
	t.Helper()
	var cerr *connect.Error
	if !errors.As(err, &cerr) || cerr.Code() != connect.CodeInvalidArgument {
		t.Fatalf("want InvalidArgument, got %v", err)
	}
	var codes []string
	for _, d := range cerr.Details() {
		msg, err := d.Value()
		if err != nil {
			t.Fatal(err)
		}
		if fv, ok := msg.(*commonv1.FieldViolations); ok {
			for _, v := range fv.Violations {
				codes = append(codes, v.Code)
			}
		}
	}
	return codes
}

func TestParseBankDetailsNormalises(t *testing.T) {
	got, err := parseBankDetails(&userv1.UpdateBankDetailsRequest{
		ClearingNumber: "8327-9",
		BankAccount:    " 123 456.789-0 ",
		BankName:       "  Swedbank ",
	})
	if err != nil {
		t.Fatal(err)
	}
	if got.ClearingNumber != "83279" || got.BankAccount != "1234567890" || got.BankName != "Swedbank" {
		t.Errorf("unexpected normalisation: %+v", got)
	}
}

func TestParseBankDetailsAllowsClearing(t *testing.T) {
	if _, err := parseBankDetails(&userv1.UpdateBankDetailsRequest{}); err != nil {
		t.Errorf("empty bank details should clear them, got %v", err)
	}
}

func TestParseBankDetailsViolations(t *testing.T) {
	tests := []struct {
		name string
		req  *userv1.UpdateBankDetailsRequest
		want []string
	}{
		{"letters", &userv1.UpdateBankDetailsRequest{ClearingNumber: "83a7", BankAccount: "12x"}, []string{"clearing_number.digits", "bank_account.digits"}},
		{"account without clearing", &userv1.UpdateBankDetailsRequest{BankAccount: "1234567"}, []string{"clearing_number.required"}},
		{"clearing without account", &userv1.UpdateBankDetailsRequest{ClearingNumber: "8327"}, []string{"bank_account.required"}},
		{"short clearing", &userv1.UpdateBankDetailsRequest{ClearingNumber: "832", BankAccount: "1234567"}, []string{"clearing_number.length"}},
		{"long account", &userv1.UpdateBankDetailsRequest{ClearingNumber: "8327", BankAccount: "12345678901234"}, []string{"bank_account.length"}},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := parseBankDetails(tt.req)
			if got := violationCodes(t, err); !slices.Equal(got, tt.want) {
				t.Errorf("got %v, want %v", got, tt.want)
			}
		})
	}
}
