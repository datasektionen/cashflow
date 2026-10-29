import { createFileRoute } from "@tanstack/react-router";
import { AccountClaim, loadAccounting } from "#/components/accounting/account-claim";
import { ClaimNotFound, ClaimSkeleton, parseNumberParam, stringifyNumberParam } from "#/components/claim/claim-route";
import { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { validateClaimPageSearch } from "#/lib/claims";

export const Route = createFileRoute("/_app/expenses/$number_/account")({
  params: { parse: parseNumberParam, stringify: stringifyNumberParam },
  validateSearch: validateClaimPageSearch,
  loader: ({ context, params }) => loadAccounting(context.queryClient, ClaimKind.EXPENSE, params.number),
  pendingComponent: ClaimSkeleton,
  notFoundComponent: ClaimNotFound,
  component: AccountExpensePage,
});

function AccountExpensePage() {
  const { number } = Route.useParams();
  const { queue } = Route.useSearch();
  // Keyed by number: the next claim starts fresh, so nothing typed carries over.
  return <AccountClaim key={number.toString()} kind={ClaimKind.EXPENSE} number={number} queue={queue} />;
}
