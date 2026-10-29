import { create } from "@bufbuild/protobuf";
import { describe, expect, it } from "vitest";
import {
  DraftRowSchema,
  FortnoxAccountSchema,
  FortnoxCostCentreSchema,
  GetVoucherDraftResponseSchema,
  VoucherRowSchema,
} from "#/gen/cashflow/accounting/v1/accounting_pb";
import { sv } from "#/lib/i18n/sv";
import { fromDraft, type RowValues, renameServerField, totals, toVoucherRows, validateRows } from "./voucher-values";

const row = (change: Partial<RowValues>): RowValues => ({
  account: "",
  costCentre: "",
  debit: "",
  credit: "",
  label: "",
  balancing: false,
  ...change,
});

describe("voucher rows", () => {
  const rows = [
    row({ account: "5460 Förbrukningsmaterial", costCentre: "ADA Ada", debit: "100,50" }),
    row({ account: "5410", debit: "20" }),
    row({ account: "2820 Skulder till medlemmar", balancing: true }),
  ];

  it("balances with the last row, whatever the others say", () => {
    expect(totals(rows)).toEqual({ debit: 12050n, credit: 12050n, balancing: 12050n });
  });

  it("becomes request rows in the same order, with codes and öre", () => {
    expect(toVoucherRows({ rows })).toEqual([
      { account: 5460, costCentre: "ADA", debitOre: 10050n, creditOre: 0n },
      { account: 5410, costCentre: "", debitOre: 2000n, creditOre: 0n },
      { account: 2820, costCentre: "", debitOre: 0n, creditOre: 12050n },
    ]);
  });

  it("flags amounts that don't parse", () => {
    expect(validateRows({ rows: [row({ debit: "12,345" })] }, sv)?.fields).toEqual({
      "rows[0].debit": sv.validation["amount.invalid"],
    });
  });

  it("maps the server's amount errors to the cell in use", () => {
    const rename = renameServerField({ rows: [row({ credit: "5" }), row({ debit: "5" }), row({ balancing: true })] });
    expect(rename("rows[0].amount")).toBe("rows[0].credit");
    expect(rename("rows[1].amount")).toBe("rows[1].debit");
    expect(rename("rows[2].amount")).toBe("rows");
    expect(rename("rows[1].account")).toBe("rows[1].account");
  });
});

describe("fromDraft", () => {
  it("labels accounts and cost centres from Fortnox's lists", () => {
    const draft = create(GetVoucherDraftResponseSchema, {
      rows: [
        create(DraftRowSchema, {
          row: create(VoucherRowSchema, { account: 5460, costCentre: "ADA", debitOre: 12345n }),
          label: "Ada › Fika",
        }),
        create(DraftRowSchema, { row: create(VoucherRowSchema, { account: 0, debitOre: 5n }) }),
        create(DraftRowSchema, {
          row: create(VoucherRowSchema, { account: 2820, creditOre: 12350n }),
          balancing: true,
        }),
      ],
    });
    const values = fromDraft(
      draft,
      [create(FortnoxAccountSchema, { number: 5460, description: "Förbrukningsmaterial" })],
      [create(FortnoxCostCentreSchema, { code: "ADA", description: "Ada" })],
      "sv",
    );
    expect(values.rows).toEqual([
      row({ account: "5460 Förbrukningsmaterial", costCentre: "ADA Ada", debit: "123,45", label: "Ada › Fika" }),
      row({ debit: "0,05" }),
      // Unknown to Fortnox: the number alone. The balancing credit is computed, not stored.
      row({ account: "2820", balancing: true }),
    ]);
  });
});
