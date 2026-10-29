import { useMutation } from "@connectrpc/connect-query";
import { problemMessage } from "#/components/claim/use-claim-action";
import { useAppForm } from "#/components/form/form";
import { applyServerErrors } from "#/components/form/server-errors";
import { CopyButton } from "#/components/ui/copy-button";
import type { AccountClaimResponse, GetVoucherDraftResponse } from "#/gen/cashflow/accounting/v1/accounting_pb";
import { accountClaim } from "#/gen/cashflow/accounting/v1/accounting-AccountingService_connectquery";
import type { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { useLocale, useT } from "#/lib/i18n";
import { formatOre } from "#/lib/money";

type Props = {
  kind: ClaimKind;
  number: bigint;
  draft: GetVoucherDraftResponse;
  onBooked: (result: AccountClaimResponse) => void;
  onProblem: (message: string) => void;
};

/**
 * For a voucher booked by hand in Fortnox: what to type there, each with a
 * copy button, and where to record the voucher number afterwards.
 */
export function ManualVoucher({ kind, number, draft, onBooked, onProblem }: Props) {
  const t = useT();
  const a = t.accounting;
  const locale = useLocale();
  const record = useMutation(accountClaim);
  const form = useAppForm({
    defaultValues: { voucherNumber: "" },
    onSubmit: async ({ value, formApi }) => {
      try {
        onBooked(
          await record.mutateAsync({
            claim: { kind, number },
            method: { case: "voucherNumber", value: value.voucherNumber },
          }),
        );
      } catch (error) {
        if (!applyServerErrors(formApi, error, t)) onProblem(problemMessage(error, t));
      }
    },
  });

  const amount = formatOre(draft.totalOre, locale);
  const facts: Array<[string, string]> = [
    [a.text, draft.description],
    [a.date, draft.transactionDate],
    [t.pay.amount, amount],
  ];

  return (
    <div className="flex flex-col gap-3">
      <p className="text-muted-foreground text-xs">{a.manualHelp}</p>
      <dl className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-3 gap-y-0.5 text-sm">
        {facts.map(([label, value]) => (
          <div key={label} className="contents">
            <dt className="text-muted-foreground text-xs">{label}</dt>
            <dd className="truncate font-medium">{value}</dd>
            <CopyButton value={value} label={label} />
          </div>
        ))}
      </dl>
      <form
        noValidate
        className="flex items-start gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void form.handleSubmit();
        }}
      >
        <div className="w-44">
          <form.AppField name="voucherNumber">
            {(field) => (
              <field.TextField
                cell
                label={a.voucherNumber}
                placeholder={a.voucherNumberPlaceholder}
                autoComplete="off"
                className="uppercase placeholder:normal-case"
              />
            )}
          </form.AppField>
        </div>
        <form.AppForm>
          <form.SubmitButton variant="outline">{a.record}</form.SubmitButton>
        </form.AppForm>
      </form>
    </div>
  );
}
