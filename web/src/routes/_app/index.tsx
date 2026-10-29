import { createQueryOptions, useQuery } from "@connectrpc/connect-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { FileText, Receipt, Trophy } from "lucide-react";
import { Amount } from "#/components/claims/badges";
import { applySearchChange, validateClaimSearch } from "#/components/claims/claim-search";
import { ClaimsList } from "#/components/claims/claims-list";
import { prefetchClaims } from "#/components/claims/claims-route";
import { WorkOverview } from "#/components/claims/work-overview";
import { Page } from "#/components/layout/page";
import { ButtonLink } from "#/components/ui/button-link";
import { Card, CardDescription, CardHeader, CardTitle } from "#/components/ui/card";
import { Skeleton } from "#/components/ui/skeleton";
import { getOverview } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { Period } from "#/gen/cashflow/stats/v1/stats_pb";
import { getPersonalStats } from "#/gen/cashflow/stats/v1/stats-StatsService_connectquery";
import { useT } from "#/lib/i18n";
import { transport } from "#/lib/rpc";

export const Route = createFileRoute("/_app/")({
  validateSearch: validateClaimSearch,
  loaderDeps: ({ search }) => search,
  loader: (args) => {
    void args.context.queryClient.prefetchQuery(createQueryOptions(getOverview, {}, { transport }));
    prefetchClaims({ mine: true })(args);
  },
  component: Overview,
});

function Overview() {
  const t = useT();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();

  return (
    <Page
      title={t.overview.title}
      actions={
        <>
          <ButtonLink variant="outline" to="/invoices/new">
            <FileText /> {t.nav.newInvoice}
          </ButtonLink>
          <ButtonLink to="/expenses/new">
            <Receipt /> {t.nav.newExpense}
          </ButtonLink>
        </>
      }
    >
      <Totals />
      <div className="mt-3">
        <WorkOverview />
      </div>
      <div className="mt-4">
        <ClaimsList
          scope={{ mine: true }}
          search={search}
          onSearch={(change) => navigate({ search: (prev) => applySearchChange(prev, change), replace: true })}
          empty={{
            icon: <Receipt />,
            title: t.overview.emptyTitle,
            body: t.overview.emptyBody,
            action: <ButtonLink to="/expenses/new">{t.overview.emptyAction}</ButtonLink>,
          }}
        />
      </div>
    </Page>
  );
}

function Totals() {
  const t = useT();
  const { data } = useQuery(getOverview, {});
  const totals = [
    { label: t.overview.awaitingAttest, ore: data?.awaitingAttestOre },
    { label: t.overview.awaitingPayment, ore: data?.awaitingPaymentOre },
    { label: t.overview.paidThisYear, ore: data?.paidThisYearOre },
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {totals.map(({ label, ore }) => (
        <Card key={label} size="sm" className="receipt-edge gap-0 rounded-b-none">
          <CardHeader>
            <CardDescription>{label}</CardDescription>
            <CardTitle className="font-medium text-xl">
              {ore === undefined ? <Skeleton className="mt-1 h-6 w-28" /> : <Amount ore={ore} />}
            </CardTitle>
          </CardHeader>
        </Card>
      ))}
      <RankTile />
    </div>
  );
}

/** Where the caller stands on this year's leaderboard; a door to the statistics. */
function RankTile() {
  const t = useT();
  const { data } = useQuery(getPersonalStats, { period: Period.YEAR });
  return (
    <Link to="/stats" className="group rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-ring">
      <Card size="sm" className="receipt-edge h-full gap-0 rounded-b-none transition-colors group-hover:bg-muted/50">
        <CardHeader>
          <CardDescription className="flex items-center gap-1.5">
            <Trophy className="size-3.5" /> {t.stats.byTotal} · {t.stats.period.year}
          </CardDescription>
          <CardTitle className="font-medium text-xl">
            {!data ? (
              <Skeleton className="mt-1 h-6 w-28" />
            ) : data.totalRank ? (
              t.stats.place(data.totalRank, data.people)
            ) : (
              <span className="text-base text-muted-foreground">{t.stats.noPlace}</span>
            )}
          </CardTitle>
        </CardHeader>
      </Card>
    </Link>
  );
}
