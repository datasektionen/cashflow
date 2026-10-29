import { createFileRoute } from "@tanstack/react-router";
import {
  ClaimNotFound,
  ClaimSkeleton,
  loadClaim,
  parseNumberParam,
  stringifyNumberParam,
} from "#/components/claim/claim-route";
import { EditClaim } from "#/components/claim-form/edit-route";
import { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";

export const Route = createFileRoute("/_app/expenses/$number_/edit")({
  params: { parse: parseNumberParam, stringify: stringifyNumberParam },
  loader: ({ context, params }) => loadClaim(context.queryClient, ClaimKind.EXPENSE, params.number),
  pendingComponent: ClaimSkeleton,
  notFoundComponent: ClaimNotFound,
  component: EditExpensePage,
});

function EditExpensePage() {
  const { number } = Route.useParams();
  return <EditClaim kind={ClaimKind.EXPENSE} number={number} />;
}
