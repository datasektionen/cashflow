import { useMutation } from "@connectrpc/connect-query";
import { useQueryClient } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { Banknote, Flag, Loader2, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { problemMessage } from "#/components/claim/use-claim-action";
import { Amount } from "#/components/claims/badges";
import { UserAvatar } from "#/components/layout/user-avatar";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "#/components/ui/alert-dialog";
import { Button } from "#/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "#/components/ui/card";
import { Checkbox } from "#/components/ui/checkbox";
import { CopyButton } from "#/components/ui/copy-button";
import type { BankDetails, CreatePayoutResponse, PendingPayout } from "#/gen/cashflow/payment/v1/payment_pb";
import { createPayout } from "#/gen/cashflow/payment/v1/payment-PaymentService_connectquery";
import { formatBankAccount } from "#/lib/bank";
import { claimLink, formatDate } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";
import { formatOre } from "#/lib/money";

/**
 * One person's expenses waiting to be paid out. Ready ones start ticked;
 * flagged ones are shown but cannot be picked. The created payout goes to
 * onCreated: the page shows it, since this card disappears once the
 * expenses are paid.
 */
export function PayoutCard({
  payout,
  onCreated,
}: {
  payout: PendingPayout;
  onCreated: (res: CreatePayoutResponse) => void;
}) {
  const t = useT();
  const locale = useLocale();
  const queryClient = useQueryClient();
  const payable = payout.expenses.filter((e) => !e.status?.flagged);
  const [selected, setSelected] = useState(() => new Set(payable.map((e) => e.number)));
  const [confirming, setConfirming] = useState(false);
  const create = useMutation(createPayout, {
    onSuccess: (res) => {
      onCreated(res);
      // Pending payouts, queues, counts and lists all change.
      void queryClient.invalidateQueries();
    },
    onError: (error) => toast.error(problemMessage(error, t)),
  });

  const name = payout.receiver?.name ?? "";
  const hasBank = Boolean(payout.bank?.clearingNumber && payout.bank.account);
  const total = payable.filter((e) => selected.has(e.number)).reduce((sum, e) => sum + e.amountOre, 0n);
  const totalText = `${formatOre(total, locale)} ${t.money.currency}`;

  const toggle = (number: bigint, on: boolean) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (on) next.add(number);
      else next.delete(number);
      return next;
    });

  return (
    <Card className="gap-0 py-0">
      <CardHeader className="flex flex-wrap items-center gap-3 border-b py-4">
        <UserAvatar
          name={name}
          username={payout.receiver?.username}
          className="bg-secondary text-secondary-foreground"
        />
        <div className="flex min-w-0 flex-1 flex-col leading-tight">
          <span className="font-medium">{name}</span>
          <span className="text-muted-foreground text-xs">{t.pay.expenseCount(payout.expenses.length)}</span>
        </div>
        {hasBank && payout.bank ? (
          <BankLine bank={payout.bank} />
        ) : (
          <span className="flex items-center gap-1.5 text-destructive-ink text-sm">
            <TriangleAlert className="size-4" /> {t.pay.missingBank}
          </span>
        )}
      </CardHeader>

      <CardContent className="px-0">
        <ul className="divide-y">
          {payout.expenses.map((e) => {
            const flagged = Boolean(e.status?.flagged);
            const id = `payout-${e.number}`;
            return (
              <li key={id} className="flex items-center gap-3 px-6 py-2.5">
                <Checkbox
                  id={id}
                  checked={!flagged && selected.has(e.number)}
                  disabled={flagged}
                  onCheckedChange={(on) => toggle(e.number, Boolean(on))}
                />
                <label htmlFor={id} className="flex min-w-0 flex-1 flex-col leading-tight">
                  <span className="truncate text-sm">{e.description}</span>
                  <span className="text-muted-foreground text-xs">
                    {flagged ? (
                      <span className="inline-flex items-center gap-1 text-destructive-ink">
                        <Flag className="size-3" /> {t.pay.flaggedNote}
                      </span>
                    ) : (
                      formatDate(e.date, locale)
                    )}
                  </span>
                </label>
                <Link
                  {...claimLink(e.kind, e.number, "pay")}
                  className="text-muted-foreground text-xs underline-offset-2 hover:underline"
                >
                  #{e.number.toString()}
                </Link>
                <Amount ore={e.amountOre} className="w-28 text-right text-sm" />
              </li>
            );
          })}
        </ul>
      </CardContent>

      <CardFooter className="justify-end gap-3 border-t py-3">
        <Button
          disabled={selected.size === 0 || !hasBank || create.isPending}
          title={selected.size === 0 ? t.pay.nothingSelected : !hasBank ? t.pay.missingBank : undefined}
          onClick={() => setConfirming(true)}
        >
          {create.isPending ? <Loader2 className="animate-spin" /> : <Banknote />}
          {t.pay.create(totalText)}
        </Button>
      </CardFooter>

      <AlertDialog open={confirming} onOpenChange={setConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.pay.confirmTitle(name)}</AlertDialogTitle>
            <AlertDialogDescription>
              {t.pay.confirmBody(t.pay.expenseCount(selected.size), totalText)}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.claim.cancel}</AlertDialogCancel>
            <AlertDialogAction onClick={() => create.mutate({ expenseNumbers: [...selected] })}>
              <Banknote /> {t.pay.confirm}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}

function BankLine({ bank }: { bank: BankDetails }) {
  const account = formatBankAccount(bank.clearingNumber, bank.account);
  return (
    <span className="flex items-center gap-1 text-sm">
      {bank.bankName && <span className="text-muted-foreground">{bank.bankName}</span>}
      <span className="amount font-medium">{account}</span>
      <CopyButton value={account} />
    </span>
  );
}

/** What to enter in the bank after creating a payout, each value one click to copy. */
export function PayoutReceipt({ result, onDone }: { result: CreatePayoutResponse; onDone: () => void }) {
  const t = useT();
  const locale = useLocale();
  const payment = result.payment;
  if (!payment) return null;
  const account = formatBankAccount(result.bank?.clearingNumber ?? "", result.bank?.account ?? "");
  const amount = formatOre(payment.totalOre, locale);
  const rows: Array<[string, string, string]> = [
    [t.pay.amount, `${amount} ${t.money.currency}`, amount],
    [t.pay.account, [result.bank?.bankName, account].filter(Boolean).join(" · "), account],
    [t.pay.reference, payment.tag, payment.tag],
  ];
  return (
    <Card className="receipt-edge relative rounded-b-none border-primary/40">
      <span className="stamp animate-stamp absolute top-5 right-5 text-primary" aria-hidden>
        {t.claims.stamp.paid}
      </span>
      <CardContent className="flex flex-col gap-4">
        <div className="pr-24">
          <h3 className="font-display font-semibold text-lg">{t.pay.createdTitle(payment.tag)}</h3>
          <p className="text-muted-foreground text-sm">{t.pay.createdBody}</p>
        </div>
        <dl className="grid gap-2 sm:max-w-md">
          {rows.map(([label, shown, copied]) => (
            <div key={label} className="flex items-center justify-between gap-3 rounded-lg bg-muted/60 px-3 py-2">
              <dt className="text-muted-foreground text-sm">{label}</dt>
              <dd className="flex items-center gap-1 font-medium amount">
                {shown}
                <CopyButton value={copied} label={label} />
              </dd>
            </div>
          ))}
        </dl>
        <div>
          <Button variant="outline" onClick={onDone}>
            {t.pay.dismiss}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
