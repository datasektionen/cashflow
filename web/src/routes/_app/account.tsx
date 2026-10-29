import { createFileRoute } from "@tanstack/react-router";
import { applySearchChange, validateClaimSearch } from "#/components/claims/claim-search";
import { prefetchClaims } from "#/components/claims/claims-route";
import { QueuePage } from "#/components/claims/queue-page";

export const Route = createFileRoute("/_app/account")({
  validateSearch: validateClaimSearch,
  loaderDeps: ({ search }) => search,
  loader: prefetchClaims({ queue: "account" }),
  component: AccountPage,
});

function AccountPage() {
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  return (
    <QueuePage
      queue="account"
      search={search}
      onSearch={(change) => navigate({ search: (prev) => applySearchChange(prev, change), replace: true })}
    />
  );
}
