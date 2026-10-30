import { useMutation } from "@connectrpc/connect-query";
import { CircleCheck, Loader2, Plus, TriangleAlert, X } from "lucide-react";
import { problemMessage } from "#/components/claim/use-claim-action";
import { Amount } from "#/components/claims/badges";
import { useAppForm } from "#/components/form/form";
import { applyServerErrors } from "#/components/form/server-errors";
import { Button } from "#/components/ui/button";
import { CopyButton } from "#/components/ui/copy-button";
import type {
  AccountClaimResponse,
  FortnoxAccount,
  FortnoxCostCentre,
  GetVoucherDraftResponse,
} from "#/gen/cashflow/accounting/v1/accounting_pb";
import { accountClaim } from "#/gen/cashflow/accounting/v1/accounting-AccountingService_connectquery";
import { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { formatDate } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";
import { formatOre } from "#/lib/money";
import { cn } from "#/lib/utils";
import {
  accountOption,
  costCentreOption,
  emptyRow,
  fromDraft,
  renameServerField,
  totals,
  toVoucherRows,
  validateRows,
} from "./voucher-values";

type Props = {
  kind: ClaimKind;
  number: bigint;
  draft: GetVoucherDraftResponse;
  accounts: FortnoxAccount[];
  costCentres: FortnoxCostCentre[];
  onBooked: (result: AccountClaimResponse) => void;
  onProblem: (message: string) => void;
};

/**
 * The voucher to book in Fortnox, prefilled from the draft. The last row is
 * the debt (2820 or 2440) and always balances the others, so the only thing
 * that can be off is the total, which the footer says in words.
 */
export function VoucherForm({ kind, number, draft, accounts, costCentres, onBooked, onProblem }: Props) {
  const t = useT();
  const a = t.accounting;
  const locale = useLocale();
  const book = useMutation(accountClaim);
  const accountOptions = accounts.map(accountOption);
  const costCentreOptions = costCentres.map(costCentreOption);

  const form = useAppForm({
    defaultValues: fromDraft(draft, accounts, costCentres, locale),
    validators: { onSubmit: ({ value }) => validateRows(value, t) },
    onSubmit: async ({ value, formApi }) => {
      try {
        const result = await book.mutateAsync({
          claim: { kind, number },
          method: { case: "rows", value: { rows: toVoucherRows(value) } },
        });
        onBooked(result);
      } catch (error) {
        if (!applyServerErrors(formApi, error, t, renameServerField(value))) onProblem(problemMessage(error, t));
      }
    },
  });

  const balancingLabel = kind === ClaimKind.INVOICE ? a.balancingInvoice : a.balancingExpense;

  return (
    <form
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        void form.handleSubmit();
      }}
      // Enter in a cell must not book the voucher by accident.
      onKeyDown={(event) => {
        if (event.key === "Enter" && event.target instanceof HTMLInputElement) event.preventDefault();
      }}
      className="flex flex-col gap-3"
    >
      <form.AppField name="rows" mode="array">
        {(rowsField) => (
          <div className="-mx-1 flex flex-col overflow-x-auto px-1">
            <table className="w-full min-w-[34rem] table-fixed text-sm">
              <caption className="sr-only">{a.fortnoxTitle}</caption>
              <colgroup>
                <col />
                <col className="w-44" />
                <col className="w-24" />
                <col className="w-24" />
                <col className="w-8" />
              </colgroup>
              <thead>
                <tr className="border-b text-left text-muted-foreground text-xs">
                  <th scope="col" className="pb-1.5 font-medium">
                    {a.columns.account}
                  </th>
                  <th scope="col" className="pb-1.5 pl-2 font-medium">
                    {a.columns.costCentre}
                  </th>
                  <th scope="col" className="pb-1.5 pl-2 text-right font-medium">
                    {a.columns.debit}
                  </th>
                  <th scope="col" className="pb-1.5 pl-2 text-right font-medium">
                    {a.columns.credit}
                  </th>
                  <td />
                </tr>
              </thead>
              <tbody>
                {rowsField.state.value.map((row, i) => (
                  <tr
                    // biome-ignore lint/suspicious/noArrayIndexKey: rows are addressed by index in the form
                    key={i}
                    className={cn(
                      "border-b border-dashed [&>td]:py-1.5 [&>td]:align-top",
                      row.balancing && "bg-muted/40",
                    )}
                  >
                    <td>
                      <div className="flex min-w-0 flex-col gap-0.5">
                        <form.AppField name={`rows[${i}].account`}>
                          {(field) => (
                            <field.ComboboxField
                              cell
                              label={`${a.row(i + 1)}: ${a.columns.account}`}
                              options={accountOptions}
                              placeholder={a.chooseAccount}
                            />
                          )}
                        </form.AppField>
                        {row.account && !accountOptions.includes(row.account) ? (
                          // A suggestion Fortnox doesn't have: say so before booking fails.
                          <span className="flex items-center gap-1 px-1 text-warning-ink text-xs">
                            <TriangleAlert className="size-3 shrink-0" /> {a.notInFortnox}
                          </span>
                        ) : (
                          <span className="truncate px-1 text-muted-foreground text-xs" title={row.label}>
                            {row.balancing ? balancingLabel : row.label}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="pl-2">
                      {row.balancing ? (
                        <span className="block px-1 pt-2 text-muted-foreground">–</span>
                      ) : (
                        <form.AppField name={`rows[${i}].costCentre`}>
                          {(field) => (
                            <field.ComboboxField
                              cell
                              clearable
                              label={`${a.row(i + 1)}: ${a.columns.costCentre}`}
                              options={costCentreOptions}
                              placeholder={a.noCostCentre}
                            />
                          )}
                        </form.AppField>
                      )}
                    </td>
                    {row.balancing ? (
                      <>
                        <td className="pt-2 pl-2 text-right text-muted-foreground">–</td>
                        <td className="pt-2 pr-3 pl-2 text-right" aria-live="polite">
                          <form.Subscribe selector={(state) => totals(state.values.rows).balancing}>
                            {(balancing) => <Amount ore={balancing} />}
                          </form.Subscribe>
                        </td>
                      </>
                    ) : (
                      (["debit", "credit"] as const).map((side) => (
                        <td key={side} className="pl-2">
                          <form.AppField name={`rows[${i}].${side}`}>
                            {(field) => (
                              <field.AmountField cell placeholder="" label={`${a.row(i + 1)}: ${a.columns[side]}`} />
                            )}
                          </form.AppField>
                        </td>
                      ))
                    )}
                    <td className="pt-1 pl-1">
                      {!row.balancing && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-xs"
                          aria-label={a.removeRow(i + 1)}
                          title={a.removeRow(i + 1)}
                          onClick={() => rowsField.removeValue(i)}
                        >
                          <X />
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <form.Subscribe selector={(state) => totals(state.values.rows)}>
                  {({ debit, credit }) => (
                    <tr className="font-medium">
                      <td className="pt-1.5">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="-ml-2"
                          // New rows go above the balancing row, which stays last.
                          onClick={() =>
                            rowsField.insertValue(Math.max(rowsField.state.value.length - 1, 0), { ...emptyRow })
                          }
                        >
                          <Plus /> {a.addRow}
                        </Button>
                      </td>
                      <td className="pt-1.5 pl-2 text-right text-muted-foreground text-xs">{a.sum}</td>
                      <td className="pt-1.5 pr-3 pl-2 text-right">
                        <Amount ore={debit} />
                      </td>
                      <td className="pt-1.5 pr-3 pl-2 text-right">
                        <Amount ore={credit} />
                      </td>
                      <td />
                    </tr>
                  )}
                </form.Subscribe>
              </tfoot>
            </table>
            {rowsField.state.meta.errors.length > 0 && (
              <p role="alert" className="pt-1 text-destructive-ink text-sm">
                {rowsField.state.meta.errors.map(String).join(" ")}
              </p>
            )}
          </div>
        )}
      </form.AppField>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-3">
        <dl className="flex flex-wrap gap-x-4 gap-y-1 text-xs">
          <Fact label={a.series} value={draft.series} />
          <Fact label={a.date} value={formatDate(draft.transactionDate, locale)} />
          <Fact label={a.text} value={draft.description} copy />
        </dl>
        <div className="flex items-center gap-3">
          <form.Subscribe selector={(state) => totals(state.values.rows).debit}>
            {(debit) =>
              debit === draft.totalOre ? (
                <span className="flex items-center gap-1.5 text-success-ink text-xs">
                  <CircleCheck className="size-3.5" /> {a.balanced}
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-warning-ink text-xs">
                  <TriangleAlert className="size-3.5" />
                  {a.totalMismatch(
                    `${formatOre(debit, locale)} ${t.money.currency}`,
                    `${formatOre(draft.totalOre, locale)} ${t.money.currency}`,
                  )}
                </span>
              )
            }
          </form.Subscribe>
          <form.Subscribe selector={(state) => state.isSubmitting}>
            {(submitting) => (
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="animate-spin" />}
                {a.book}
              </Button>
            )}
          </form.Subscribe>
        </div>
      </div>
    </form>
  );
}

function Fact({ label, value, copy = false }: { label: string; value: string; copy?: boolean }) {
  return (
    <div className="flex min-w-0 items-center gap-1">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="truncate font-medium">{value}</dd>
      {copy && <CopyButton value={value} label={label} />}
    </div>
  );
}
