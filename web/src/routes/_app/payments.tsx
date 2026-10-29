import { useQuery } from "@connectrpc/connect-query";
import { useDebouncedCallback } from "@tanstack/react-pacer";
import { keepPreviousData } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, SearchIcon, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { Amount } from "#/components/claims/badges";
import { Page } from "#/components/layout/page";
import { StateCard } from "#/components/layout/states";
import { Button } from "#/components/ui/button";
import { Card } from "#/components/ui/card";
import { CopyButton } from "#/components/ui/copy-button";
import { Input } from "#/components/ui/input";
import { Skeleton } from "#/components/ui/skeleton";
import { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { listPayments } from "#/gen/cashflow/payment/v1/payment-PaymentService_connectquery";
import { claimLink, formatDate } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";

const PAGE_SIZE = 25;

export const Route = createFileRoute("/_app/payments")({
  validateSearch: (raw: Record<string, unknown>): { q?: string; page?: number } => ({
    q: typeof raw.q === "string" && raw.q.trim() ? raw.q : undefined,
    page: typeof raw.page === "number" && Number.isInteger(raw.page) && raw.page > 1 ? raw.page : undefined,
  }),
  component: PaymentsPage,
});

/** Every payout, newest first; searchable by the bank reference. */
function PaymentsPage() {
  const t = useT();
  const locale = useLocale();
  const { q, page = 1 } = Route.useSearch();
  const navigate = Route.useNavigate();
  const query = useQuery(listPayments, { query: q, page, pageSize: PAGE_SIZE }, { placeholderData: keepPreviousData });
  const payments = query.data?.payments ?? [];
  const total = query.data?.total ?? 0;
  const c = t.payments.columns;

  const [text, setText] = useState(q ?? "");
  useEffect(() => setText(q ?? ""), [q]);
  const commit = useDebouncedCallback(
    (value: string) => navigate({ search: { q: value.trim() || undefined }, replace: true }),
    { wait: 250 },
  );

  return (
    <Page title={t.payments.title}>
      <div className="flex flex-col gap-4">
        <div className="relative md:max-w-sm">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            className="pl-8"
            value={text}
            placeholder={t.payments.search}
            aria-label={t.payments.search}
            onChange={(event) => {
              setText(event.target.value);
              commit(event.target.value);
            }}
          />
        </div>
        <Card className="gap-0 overflow-x-auto p-0">
          {query.isPending ? (
            <Skeleton className="m-4 h-40" />
          ) : payments.length === 0 ? (
            <StateCard
              className="m-4 border-0"
              icon={<Wallet />}
              title={q ? t.claims.noMatchesTitle : t.payments.title}
              description={q ? t.payments.noMatches : t.payments.empty}
            />
          ) : (
            <table className="w-full min-w-[44rem] text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground text-xs">
                  <th className="h-10 px-4 font-medium">{c.reference}</th>
                  <th className="px-3 font-medium">{c.date}</th>
                  <th className="px-3 font-medium">{c.receiver}</th>
                  <th className="px-3 font-medium">{c.expenses}</th>
                  <th className="px-3 text-right font-medium">{c.amount}</th>
                  <th className="px-4 font-medium">{c.payer}</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={p.id.toString()} className="border-b last:border-0">
                    <td className="h-12 px-4">
                      <span className="flex items-center gap-1 font-medium amount">
                        {p.tag}
                        <CopyButton value={p.tag} />
                      </span>
                    </td>
                    <td className="px-3 text-muted-foreground">{formatDate(p.date, locale)}</td>
                    <td className="px-3">{p.receiver?.name}</td>
                    <td className="px-3">
                      <span className="flex flex-wrap gap-x-2">
                        {p.expenseNumbers.map((n) => (
                          <Link
                            key={n.toString()}
                            {...claimLink(ClaimKind.EXPENSE, n)}
                            className="text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
                          >
                            #{n.toString()}
                          </Link>
                        ))}
                      </span>
                    </td>
                    <td className="px-3 text-right">
                      <Amount ore={p.totalOre} />
                    </td>
                    <td className="px-4 text-muted-foreground">{p.payer?.name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
        {total > PAGE_SIZE && (
          <div className="flex items-center justify-end gap-3 text-muted-foreground text-sm">
            {t.claims.range((page - 1) * PAGE_SIZE + 1, Math.min(page * PAGE_SIZE, total), total)}
            <Button
              variant="outline"
              size="icon-sm"
              aria-label={t.claims.previous}
              disabled={page <= 1}
              onClick={() => navigate({ search: (s) => ({ ...s, page: page - 1 > 1 ? page - 1 : undefined }) })}
            >
              <ChevronLeft />
            </Button>
            <Button
              variant="outline"
              size="icon-sm"
              aria-label={t.claims.next}
              disabled={page * PAGE_SIZE >= total}
              onClick={() => navigate({ search: (s) => ({ ...s, page: page + 1 }) })}
            >
              <ChevronRight />
            </Button>
          </div>
        )}
      </div>
    </Page>
  );
}
