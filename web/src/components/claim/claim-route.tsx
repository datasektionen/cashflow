import { Code, ConnectError } from "@connectrpc/connect";
import { createQueryOptions } from "@connectrpc/connect-query";
import type { QueryClient } from "@tanstack/react-query";
import { notFound } from "@tanstack/react-router";
import { SearchX } from "lucide-react";
import { StateCard } from "#/components/layout/states";
import { ButtonLink } from "#/components/ui/button-link";
import { Card, CardContent } from "#/components/ui/card";
import { Skeleton } from "#/components/ui/skeleton";
import type { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { getClaim } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { useT } from "#/lib/i18n";
import { transport } from "#/lib/rpc";

/** Claim numbers in URLs: positive integers only, anything else is a 404. */
export function parseNumberParam({ number }: { number: string }): { number: bigint } {
  if (!/^\d{1,15}$/.test(number) || BigInt(number) === 0n) throw notFound();
  return { number: BigInt(number) };
}

export function stringifyNumberParam({ number }: { number: bigint }) {
  return { number: number.toString() };
}

/** Waits for the claim, so the page opens complete; unknown or hidden claims become a 404. */
export async function loadClaim(queryClient: QueryClient, kind: ClaimKind, number: bigint) {
  try {
    await queryClient.ensureQueryData(createQueryOptions(getClaim, { kind, number }, { transport }));
  } catch (error) {
    if (ConnectError.from(error).code === Code.NotFound) throw notFound();
    throw error;
  }
}

export function ClaimNotFound() {
  const t = useT();
  return (
    <main className="mx-auto w-full max-w-3xl p-6 md:p-10">
      <StateCard
        icon={<SearchX />}
        title={t.claim.notFoundTitle}
        description={t.claim.notFoundBody}
        action={<ButtonLink to="/">{t.errors.home}</ButtonLink>}
      />
    </main>
  );
}

export function ClaimSkeleton() {
  return (
    <main className="mx-auto w-full max-w-7xl p-4 md:p-8" aria-busy="true">
      <Skeleton className="h-8 w-28" />
      <div className="mt-4 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
        <Card>
          <CardContent className="flex flex-col gap-4">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-2/3" />
            <Skeleton className="h-10 w-48" />
            <Skeleton className="h-16 w-full" />
          </CardContent>
        </Card>
        <Skeleton className="hidden h-[60vh] rounded-xl lg:block" />
      </div>
    </main>
  );
}
