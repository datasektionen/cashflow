import { createQueryOptions } from "@connectrpc/connect-query";
import { createFileRoute } from "@tanstack/react-router";
import { ClaimForm } from "#/components/claim-form/claim-form";
import { getBudget } from "#/gen/cashflow/budget/v1/budget-BudgetService_connectquery";
import { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { transport } from "#/lib/rpc";

export const Route = createFileRoute("/_app/invoices/new")({
  // The budget pickers' data starts loading before the form shows.
  loader: ({ context }) => void context.queryClient.prefetchQuery(createQueryOptions(getBudget, {}, { transport })),
  component: () => <ClaimForm kind={ClaimKind.INVOICE} />,
});
