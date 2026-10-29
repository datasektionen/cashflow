import { ConnectError, createClient } from "@connectrpc/connect";
import { createConnectQueryKey, useTransport } from "@connectrpc/connect-query";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { toast } from "sonner";
import { type Claim, type ClaimKind, ClaimService } from "#/gen/cashflow/claim/v1/claim_pb";
import { getClaim } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { ProblemSchema } from "#/gen/cashflow/common/v1/errors_pb";
import { type Messages, useT } from "#/lib/i18n";

/** The translated message for a failed claim action. */
export function problemMessage(error: unknown, t: Messages): string {
  const code = ConnectError.from(error).findDetails(ProblemSchema)[0]?.code;
  return (code && t.problems[code]) || t.problems.unknown;
}

type Action = {
  /** Names the action, so the UI can show which button is busy. */
  key: string;
  call: () => Promise<{ claim?: Claim } | object>;
  done: string;
};

/**
 * Runs workflow actions on one claim. The server answers with the claim as it
 * is afterwards, which replaces the cached copy at once; lists, queue counts
 * and totals refetch in the background. Rule problems become a toast in the
 * user's language.
 */
export function useClaimAction(kind: ClaimKind, number: bigint) {
  const t = useT();
  const queryClient = useQueryClient();
  const transport = useTransport();
  const client = useMemo(() => createClient(ClaimService, transport), [transport]);

  const mutation = useMutation({
    mutationFn: (action: Action) => action.call(),
    onSuccess: (result, action) => {
      if ("claim" in result && result.claim) {
        queryClient.setQueryData(
          createConnectQueryKey({ schema: getClaim, input: { kind, number }, transport, cardinality: "finite" }),
          (old) => (old ? { ...old, claim: result.claim } : old),
        );
      }
      void queryClient.invalidateQueries({
        queryKey: createConnectQueryKey({ schema: ClaimService, transport, cardinality: undefined }),
        // The claim itself is fresh from the response above.
        predicate: (query) => (query.queryKey[1] as { methodName?: string })?.methodName !== getClaim.name,
      });
      toast.success(action.done);
    },
    onError: (error) => toast.error(problemMessage(error, t)),
  });

  return {
    /** The claim service, for building actions. */
    client,
    run: (action: Action) => mutation.mutateAsync(action).catch(() => undefined),
    /** The key of the running action, if any. */
    pending: mutation.isPending ? mutation.variables?.key : undefined,
  };
}
