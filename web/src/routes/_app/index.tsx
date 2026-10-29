import { createQueryOptions, useQuery } from "@connectrpc/connect-query";
import { createFileRoute } from "@tanstack/react-router";
import { FileText, Receipt } from "lucide-react";
import { Amount } from "#/components/claims/badges";
import { applySearchChange, validateClaimSearch } from "#/components/claims/claim-search";
import { ClaimsList } from "#/components/claims/claims-list";
import { prefetchClaims } from "#/components/claims/claims-route";
import { Page } from "#/components/layout/page";
import { ButtonLink } from "#/components/ui/button-link";
import { Card, CardDescription, CardHeader, CardTitle } from "#/components/ui/card";
import { Skeleton } from "#/components/ui/skeleton";
import { getOverview } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
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
  const me = useQuery(getMe, {});
  const firstName = me.data?.user?.name.split(" ")[0] ?? "";

  return (
    <Page
      eyebrow={t.overview.greeting(firstName)}
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
      <div className="mt-8">
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
    <div className="grid gap-4 sm:grid-cols-3">
      {totals.map(({ label, ore }) => (
        <Card key={label} className="receipt-edge gap-0 rounded-b-none">
          <CardHeader>
            <CardDescription>{label}</CardDescription>
            <CardTitle className="font-medium text-2xl">
              {ore === undefined ? <Skeleton className="mt-1 h-7 w-32" /> : <Amount ore={ore} />}
            </CardTitle>
          </CardHeader>
        </Card>
      ))}
    </div>
  );
}
