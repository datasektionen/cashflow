import { useQuery } from "@connectrpc/connect-query";
import { createFileRoute } from "@tanstack/react-router";
import { Banknote, CircleCheckBig } from "lucide-react";
import { useState } from "react";
import { applySearchChange, validateClaimSearch } from "#/components/claims/claim-search";
import { ClaimsList } from "#/components/claims/claims-list";
import { prefetchClaims } from "#/components/claims/claims-route";
import { Page } from "#/components/layout/page";
import { StateCard } from "#/components/layout/states";
import { PayoutCard, PayoutReceipt } from "#/components/payments/payout-card";
import { Skeleton } from "#/components/ui/skeleton";
import type { CreatePayoutResponse } from "#/gen/cashflow/payment/v1/payment_pb";
import { listPendingPayouts } from "#/gen/cashflow/payment/v1/payment-PaymentService_connectquery";
import { useT } from "#/lib/i18n";

export const Route = createFileRoute("/_app/pay")({
  validateSearch: validateClaimSearch,
  loaderDeps: ({ search }) => search,
  loader: prefetchClaims({ queue: "pay" }),
  component: PayPage,
});

/** Expenses are paid out per person in one transfer; invoices one by one. */
function PayPage() {
  const t = useT();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const pending = useQuery(listPendingPayouts, {});
  // Created payouts stay on screen until dismissed: their bank details are
  // still needed after the expenses have left the pending list.
  const [created, setCreated] = useState<CreatePayoutResponse[]>([]);

  return (
    <Page title={t.queues.pay.title}>
      <section aria-labelledby="payouts" className="flex flex-col gap-4">
        <div>
          <h2 id="payouts" className="font-display font-semibold text-xl">
            {t.pay.expensesTitle}
          </h2>
          <p className="text-muted-foreground text-sm">{t.pay.expensesHelp}</p>
        </div>
        {created.map((res) => (
          <PayoutReceipt
            key={res.payment?.id.toString()}
            result={res}
            onDone={() => setCreated((list) => list.filter((r) => r !== res))}
          />
        ))}
        {pending.isPending ? (
          <Skeleton className="h-48 rounded-xl" />
        ) : pending.data?.payouts.length ? (
          pending.data.payouts.map((payout) => (
            <PayoutCard
              key={payout.receiver?.username}
              payout={payout}
              onCreated={(res) => setCreated((list) => [res, ...list])}
            />
          ))
        ) : (
          <StateCard icon={<CircleCheckBig />} title={t.queues.pay.emptyTitle} description={t.pay.noExpenses} />
        )}
      </section>

      <section aria-labelledby="invoices" className="mt-12 flex flex-col gap-4">
        <h2 id="invoices" className="font-display font-semibold text-xl">
          {t.pay.invoicesTitle}
        </h2>
        <ClaimsList
          scope={{ queue: "pay" }}
          kind="invoice"
          search={search}
          onSearch={(change) => navigate({ search: (prev) => applySearchChange(prev, change), replace: true })}
          empty={{ icon: <Banknote />, title: t.queues.pay.emptyTitle, body: t.queues.pay.emptyBody }}
        />
      </section>
    </Page>
  );
}
