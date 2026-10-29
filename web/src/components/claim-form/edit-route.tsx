import { useSuspenseQuery } from "@connectrpc/connect-query";
import { Lock } from "lucide-react";
import { StateCard } from "#/components/layout/states";
import { ButtonLink } from "#/components/ui/button-link";
import type { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { getClaim } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { claimLink } from "#/lib/claims";
import { useT } from "#/lib/i18n";
import { ClaimForm } from "./claim-form";

/**
 * The edit form for a claim, or a plain explanation when it can't be edited
 * any more (paid, or someone else's), with the way back.
 */
export function EditClaim({ kind, number }: { kind: ClaimKind; number: bigint }) {
  const t = useT();
  const { data } = useSuspenseQuery(getClaim, { kind, number });
  const claim = data.claim;
  if (!claim?.actions?.edit) {
    return (
      <main className="mx-auto w-full max-w-3xl p-6 md:p-10">
        <StateCard
          icon={<Lock />}
          title={t.claimForm.cannotEditTitle}
          description={t.claimForm.cannotEditBody}
          action={<ButtonLink {...claimLink(kind, number)}>{t.claimForm.backToClaim}</ButtonLink>}
        />
      </main>
    );
  }
  return <ClaimForm kind={kind} claim={claim} />;
}
