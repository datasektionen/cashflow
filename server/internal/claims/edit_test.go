package claims

import (
	"context"
	"errors"
	"slices"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgtype"

	"github.com/datasektionen/cashflow/server/internal/database/db"
	"github.com/datasektionen/cashflow/server/internal/hive"
	"github.com/datasektionen/cashflow/server/internal/perm"
)

func (f *fixtures) upload(id, uploader string) string {
	f.t.Helper()
	if _, err := f.pool.Exec(context.Background(), `INSERT INTO cashflow4_uploads (id, uploader, storage_key, filename, content_type, size_bytes)
		VALUES ($1, $2, 'c4/' || $1 || '/kvitto.jpg', 'kvitto.jpg', 'image/jpeg', 10)`, id, uploader); err != nil {
		f.t.Fatal(err)
	}
	return id
}

func codes(err error) []string {
	var invalid *InvalidInput
	if !errors.As(err, &invalid) {
		return nil
	}
	var out []string
	for _, v := range invalid.Violations {
		out = append(out, v.Field+":"+v.Code)
	}
	return out
}

func TestCreateValidation(t *testing.T) {
	s, f := testStore(t)
	f.profile("anna")
	future := time.Now().AddDate(0, 0, 3)
	_, err := s.Create(context.Background(), viewer("anna", nil), Expense, Input{
		Description: "  ",
		Date:        &future,
		Parts:       []PartInput{{CostCentre: "Ada", AmountOre: 0}},
	})
	want := []string{
		"description:description.required", "date:date.future",
		"parts[0].secondary_cost_centre:secondary_cost_centre.required", "parts[0].budget_line:budget_line.required",
		"parts[0].amount_ore:amount.positive", "files:files.required",
	}
	if got := codes(err); !slices.Equal(got, want) {
		t.Errorf("got %v\nwant %v", got, want)
	}
	_, err = s.Create(context.Background(), viewer("anna", nil), Invoice, Input{Description: "Hyra", Parts: []PartInput{{"Ada", "Allmänt", "Hyra", 100}}, UploadIDs: []string{"x"}})
	if got := codes(err); !slices.Equal(got, []string{"invoice_number:invoice_number.required"}) {
		t.Errorf("invoice: %v", got)
	}
}

func TestCreateAndEdit(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	f.profile("anna")
	f.profile("kassor")
	anna := viewer("anna", nil)
	treasurer := viewer("kassor", map[string]hive.Grant{perm.Confirm: all, perm.Attest: all, perm.Pay: all})
	day := time.Date(2026, 9, 1, 0, 0, 0, 0, time.UTC)
	parts := []PartInput{{"Ada", "Allmänt", "Fika", 12345}, {"DSys", "Drift", "Servrar", 55}}

	// Someone else's upload cannot be attached.
	f.upload("theirs", "bertil")
	if _, err := s.Create(ctx, anna, Expense, Input{Description: "Fika", Date: &day, Parts: parts, UploadIDs: []string{"theirs"}}); !slices.Equal(codes(err), []string{"files:files.unknown_upload"}) {
		t.Fatalf("attaching another's upload: %v", err)
	}

	n, err := s.Create(ctx, anna, Expense, Input{Description: " Fika ", Date: &day, Parts: parts, UploadIDs: []string{f.upload("u1", "anna")}})
	if err != nil {
		t.Fatal(err)
	}
	c, _ := s.Get(ctx, anna, Expense, n)
	if c.Description != "Fika" || c.AmountOre != 12400 || c.Owner.Username != "anna" {
		t.Fatalf("created %+v", c)
	}
	// An upload attaches once.
	if _, err := s.Create(ctx, anna, Expense, Input{Description: "Igen", Date: &day, Parts: parts, UploadIDs: []string{"u1"}}); err == nil {
		t.Error("an attached upload must not attach again")
	}

	// Attest, confirm and flag, then edit only the description: attestations
	// and confirmation survive, the flag goes.
	state, _ := s.State(ctx, treasurer, c)
	for _, p := range state.Parts {
		if err := s.SetAttested(ctx, treasurer, Expense, n, p.ID, true); err != nil {
			t.Fatal(err)
		}
	}
	if err := s.SetConfirmed(ctx, treasurer, n, true); err != nil {
		t.Fatal(err)
	}
	if err := s.SetFlagged(ctx, treasurer, n, true); err != nil {
		t.Fatal(err)
	}
	if err := s.Update(ctx, anna, Expense, n, Input{Description: "Fika till mötet", Date: &day, Parts: parts}); err != nil {
		t.Fatal(err)
	}
	c, _ = s.Get(ctx, anna, Expense, n)
	if c.Description != "Fika till mötet" || !c.Attested || !c.Confirmed || c.Flagged {
		t.Errorf("after a description edit: %+v", c)
	}

	// Adding a file voids the confirmation but keeps the attestations.
	if err := s.Update(ctx, anna, Expense, n, Input{Description: c.Description, Date: &day, Parts: parts, UploadIDs: []string{f.upload("u2", "anna")}}); err != nil {
		t.Fatal(err)
	}
	c, _ = s.Get(ctx, anna, Expense, n)
	if !c.Attested || c.Confirmed {
		t.Errorf("after adding a file: %+v", c)
	}

	// Changing an amount replaces the parts, so they need attesting again.
	changed := slices.Clone(parts)
	changed[1].AmountOre = 100
	if err := s.Update(ctx, anna, Expense, n, Input{Description: c.Description, Date: &day, Parts: changed}); err != nil {
		t.Fatal(err)
	}
	c, _ = s.Get(ctx, anna, Expense, n)
	if c.Attested || c.AmountOre != 12445 {
		t.Errorf("after changing parts: %+v", c)
	}

	// Only the owner edits, and not once paid.
	if err := s.Update(ctx, treasurer, Expense, n, Input{Description: "x", Date: &day, Parts: parts}); !errors.Is(err, ErrNotPermitted) {
		t.Errorf("treasurer editing: %v", err)
	}
	paid := f.add(claimSpec{kind: Expense, owner: "anna", confirmed: true, paid: true, parts: []partSpec{{"Ada", 100, true}}})
	if err := s.Update(ctx, anna, Expense, paid, Input{Description: "x", Date: &day, Parts: parts}); !errors.Is(err, ErrAlreadyPaid) {
		t.Errorf("editing a paid expense: %v", err)
	}
}

func TestBudgetUsage(t *testing.T) {
	s, f := testStore(t)
	ctx := context.Background()
	in2026 := time.Date(2026, 3, 1, 0, 0, 0, 0, time.UTC)
	f.add(claimSpec{kind: Expense, owner: "anna", date: in2026, parts: []partSpec{{"Ada", 1000, true}}})
	f.add(claimSpec{kind: Expense, owner: "anna", date: in2026, parts: []partSpec{{" ada ", 250, false}}})
	excluded := f.add(claimSpec{kind: Expense, owner: "anna", date: in2026, parts: []partSpec{{"Ada", 99999, false}}})
	f.add(claimSpec{kind: Expense, owner: "anna", date: time.Date(2025, 12, 31, 0, 0, 0, 0, time.UTC), parts: []partSpec{{"Ada", 5000, false}}})

	c, _ := s.Get(ctx, viewer("anna", nil), Expense, excluded)
	rows, err := s.Queries.BudgetUsage(ctx, db.BudgetUsageParams{
		FromDate:       pgtype.Date{Time: time.Date(2026, 1, 1, 0, 0, 0, 0, time.UTC), Valid: true},
		ToDate:         pgtype.Date{Time: time.Date(2027, 1, 1, 0, 0, 0, 0, time.UTC), Valid: true},
		ExcludeClaimID: c.ID,
	})
	if err != nil {
		t.Fatal(err)
	}
	// Names match case- and space-insensitively; other years and the
	// excluded claim don't count.
	if len(rows) != 1 || rows[0].CostCentre != "ada" || rows[0].UploadedOre != 1250 || rows[0].AttestedOre != 1000 {
		t.Errorf("usage %+v", rows)
	}
}
