import { useQuery } from "@connectrpc/connect-query";
import { createFileRoute } from "@tanstack/react-router";
import { ScrollText } from "lucide-react";
import { applySearchChange, validateClaimSearch } from "#/components/claims/claim-search";
import { ClaimsList } from "#/components/claims/claims-list";
import { prefetchClaims } from "#/components/claims/claims-route";
import { Page } from "#/components/layout/page";
import { ToggleGroup, ToggleGroupItem } from "#/components/ui/toggle-group";
import { listVoucherSeries } from "#/gen/cashflow/accounting/v1/accounting-AccountingService_connectquery";
import { useT } from "#/lib/i18n";

export const Route = createFileRoute("/_app/vouchers")({
  validateSearch: validateClaimSearch,
  loaderDeps: ({ search }) => search,
  loader: prefetchClaims({ accounted: true }),
  component: VouchersPage,
});

/** Everything accounted, by voucher: searchable by number ("E12"), filterable by series. */
function VouchersPage() {
  const t = useT();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const series = useQuery(listVoucherSeries, {}, { staleTime: 60 * 60 * 1000 });
  const onSearch = (change: Parameters<typeof applySearchChange>[1]) =>
    navigate({ search: (prev) => applySearchChange(prev, change), replace: true });

  return (
    <Page title={t.vouchers.title}>
      <ClaimsList
        scope={{ accounted: true }}
        search={search}
        onSearch={onSearch}
        searchPlaceholder={t.vouchers.search}
        hideFlags={["accounted"]}
        empty={{ icon: <ScrollText />, title: t.vouchers.emptyTitle, body: t.vouchers.emptyBody }}
        toolbar={
          series.data &&
          series.data.series.length > 1 && (
            <ToggleGroup
              variant="outline"
              value={[search.series ?? "all"]}
              onValueChange={(value: string[]) => {
                const code = value[0];
                if (code) onSearch({ series: code === "all" ? undefined : code });
              }}
            >
              <ToggleGroupItem value="all" className="px-3">
                {t.vouchers.allSeries}
              </ToggleGroupItem>
              {series.data.series.map((s) => (
                <ToggleGroupItem
                  key={s.code}
                  value={s.code}
                  className="px-3"
                  title={s.inFortnox ? s.description : t.vouchers.notInFortnox}
                >
                  {s.code}
                </ToggleGroupItem>
              ))}
            </ToggleGroup>
          )
        }
      />
    </Page>
  );
}
