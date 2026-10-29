package rpc

import (
	"errors"

	"connectrpc.com/connect"

	commonv1 "github.com/datasektionen/cashflow/server/gen/cashflow/common/v1"
)

// violations collects field errors while validating a request. Codes are
// stable identifiers the frontend translates, not user-facing text.
type violations []*commonv1.FieldViolation

func (v *violations) add(field, code string) {
	*v = append(*v, &commonv1.FieldViolation{Field: field, Code: code})
}

// err returns an InvalidArgument error carrying the violations, or nil.
func (v violations) err() error {
	if len(v) == 0 {
		return nil
	}
	cerr := connect.NewError(connect.CodeInvalidArgument, errors.New("invalid request"))
	if detail, err := connect.NewErrorDetail(&commonv1.FieldViolations{Violations: v}); err == nil {
		cerr.AddDetail(detail)
	}
	return cerr
}
