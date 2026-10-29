import { createFileRoute } from "@tanstack/react-router";
import { applySearchChange, validateClaimSearch } from "#/components/claims/claim-search";
import { prefetchClaims } from "#/components/claims/claims-route";
import { QueuePage } from "#/components/claims/queue-page";

export const Route = createFileRoute("/_app/claims")({
  validateSearch: validateClaimSearch,
  loaderDeps: ({ search }) => search,
  loader: prefetchClaims({}),
  component: AllClaimsPage,
});

function AllClaimsPage() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  return (
    <QueuePage
      queue="all"
      search={search}
      onSearch={(change) => navigate({ search: (prev) => applySearchChange(prev, change), replace: true })}
    />
  );
}
