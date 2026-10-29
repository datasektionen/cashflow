import { createFileRoute } from "@tanstack/react-router";
import { ClaimDetail } from "#/components/claim/claim-detail";
import {
  ClaimNotFound,
  ClaimSkeleton,
  loadClaim,
  parseNumberParam,
  stringifyNumberParam,
} from "#/components/claim/claim-route";
import { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { validateClaimPageSearch } from "#/lib/claims";

export const Route = createFileRoute("/_app/expenses/$number")({
  params: { parse: parseNumberParam, stringify: stringifyNumberParam },
  validateSearch: validateClaimPageSearch,
  loader: ({ context, params }) => loadClaim(context.queryClient, ClaimKind.EXPENSE, params.number),
  pendingComponent: ClaimSkeleton,
  notFoundComponent: ClaimNotFound,
  component: ExpensePage,
});

function ExpensePage() {
  const { number } = Route.useParams();
  const { queue } = Route.useSearch();
  return <ClaimDetail kind={ClaimKind.EXPENSE} number={number} queue={queue} />;
}
