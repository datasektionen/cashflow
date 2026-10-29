import { createQueryOptions } from "@connectrpc/connect-query";
import type { QueryClient } from "@tanstack/react-query";
import { listClaims } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { transport } from "#/lib/rpc";
import { type ClaimScope, type ClaimSearch, listRequest } from "./claim-search";

/**
 * A loader for routes showing a claims list. It starts the fetch without
 * waiting for it: the page appears at once and the list fills in (or keeps
 * the previous rows while a filter changes). On hover-preload the data is
 * usually ready before the click.
 */
export function prefetchClaims(scope: ClaimScope) {
  return ({ context, deps }: { context: { queryClient: QueryClient }; deps: ClaimSearch }) => {
    void context.queryClient.prefetchQuery(createQueryOptions(listClaims, listRequest(scope, deps), { transport }));
  };
}
