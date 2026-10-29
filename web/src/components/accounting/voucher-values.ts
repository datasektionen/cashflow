import type {
  FortnoxAccount,
  FortnoxCostCentre,
  GetVoucherDraftResponse,
  VoucherRow,
} from "#/gen/cashflow/accounting/v1/accounting_pb";
import type { Locale, Messages } from "#/lib/i18n";
import { oreToInput, parseKronor } from "#/lib/money";

/**
 * One voucher row as the form holds it. Account and cost centre are the
 * picker's option labels ("5460 Förbrukningsmaterial", "ADA Ada"), amounts
 * the text typed. The balancing row's credit is not stored: it is always
 * whatever makes the voucher balance.
 */
export type RowValues = {
  account: string;
  costCentre: string;
  debit: string;
  credit: string;
  /** Where a suggested row comes from, e.g. "Ada › Kärnverksamhet › Fika". */
  label: string;
  balancing: boolean;
};

export type VoucherFormValues = { rows: RowValues[] };

export const accountOption = (a: Pick<FortnoxAccount, "number" | "description">) =>
  a.description ? `${a.number} ${a.description}` : String(a.number);
export const costCentreOption = (c: Pick<FortnoxCostCentre, "code" | "description">) =>
  c.description ? `${c.code} ${c.description}` : c.code;

/** The account number in an option label; 0 when none is chosen. */
export const accountNumber = (option: string) => Number.parseInt(option, 10) || 0;
/** The cost centre code in an option label. */
export const costCentreCode = (option: string) => option.split(" ")[0] ?? "";

export const emptyRow: RowValues = { account: "", costCentre: "", debit: "", credit: "", label: "", balancing: false };

/** The draft as form values, with labels from Fortnox's lists where known. */
export function fromDraft(
  draft: GetVoucherDraftResponse,
  accounts: FortnoxAccount[],
  costCentres: FortnoxCostCentre[],
  locale: Locale,
): VoucherFormValues {
  const account = (n: number) => {
    const known = accounts.find((a) => a.number === n);
    return n === 0 ? "" : known ? accountOption(known) : String(n);
  };
  const costCentre = (code: string) => {
    const known = costCentres.find((c) => c.code === code);
    return known ? costCentreOption(known) : code;
  };
  return {
    rows: draft.rows.map(({ row, label, balancing }) => ({
      account: account(row?.account ?? 0),
      costCentre: costCentre(row?.costCentre ?? ""),
      debit: row?.debitOre ? oreToInput(row.debitOre, locale) : "",
      credit: row?.creditOre && !balancing ? oreToInput(row.creditOre, locale) : "",
      label,
      balancing,
    })),
  };
}

const ore = (text: string) => (text.trim() ? (parseKronor(text) ?? 0n) : 0n);

/** Debit and credit of the rows the user edits; the balancing row evens them out. */
export function totals(rows: RowValues[]) {
  let debit = 0n;
  let credit = 0n;
  for (const row of rows) {
    if (row.balancing) continue;
    debit += ore(row.debit);
    credit += ore(row.credit);
  }
  const balancing = debit - credit;
  return { debit, credit: credit + balancing, balancing };
}

/** The rows as the server takes them, in the same order, so errors map back by index. */
export function toVoucherRows(values: VoucherFormValues): Omit<VoucherRow, "$typeName">[] {
  const { balancing } = totals(values.rows);
  return values.rows.map((row) => ({
    account: accountNumber(row.account),
    costCentre: row.balancing ? "" : costCentreCode(row.costCentre),
    debitOre: row.balancing ? 0n : ore(row.debit),
    creditOre: row.balancing ? balancing : ore(row.credit),
  }));
}

/** Amounts that don't parse, which only the browser can see. */
export function validateRows(values: VoucherFormValues, t: Messages) {
  const fields: Record<string, string> = {};
  values.rows.forEach((row, i) => {
    for (const side of ["debit", "credit"] as const) {
      if (row[side].trim() && parseKronor(row[side]) === undefined)
        fields[`rows[${i}].${side}`] = t.validation["amount.invalid"] ?? "";
    }
  });
  return Object.keys(fields).length ? { fields } : undefined;
}

/**
 * Server field names to form field names: "rows[2].amount" is the debit or
 * credit cell, whichever the row uses; a balancing row's amount is the
 * voucher's problem as a whole.
 */
export function renameServerField(values: VoucherFormValues) {
  return (field: string) => {
    const match = /^rows\[(\d+)\]\.amount$/.exec(field);
    if (!match) return field;
    const row = values.rows[Number(match[1])];
    if (!row || row.balancing) return "rows";
    return `rows[${match[1]}].${row.credit.trim() && !row.debit.trim() ? "credit" : "debit"}`;
  };
}
