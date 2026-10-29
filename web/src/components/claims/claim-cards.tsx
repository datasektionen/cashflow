import { Link } from "@tanstack/react-router";
import type { ClaimSummary } from "#/gen/cashflow/claim/v1/claim_pb";
import { claimLink, formatDate, type QueueSlug } from "#/lib/claims";
import { useLocale } from "#/lib/i18n";
import { Amount, CostCentreChip, KindIcon, StageBadge } from "./badges";

/** The claims list on small screens: one tappable card per claim. */
export function ClaimCards({
  claims,
  showOwner,
  queue,
}: {
  claims: ClaimSummary[];
  showOwner: boolean;
  queue?: QueueSlug;
}) {
  const locale = useLocale();
  return (
    <ul className="divide-y">
      {claims.map((claim) => (
        <li key={`${claim.kind}-${claim.number}`}>
          <Link
            {...claimLink(claim.kind, claim.number, queue)}
            className="flex flex-col gap-2 px-4 py-3 outline-none transition-colors active:bg-muted focus-visible:bg-accent"
          >
            <div className="flex items-start justify-between gap-3">
              <span className="flex min-w-0 items-center gap-2">
                <KindIcon kind={claim.kind} />
                <span className="truncate font-medium">{claim.description}</span>
              </span>
              <Amount ore={claim.amountOre} className="font-medium" />
            </div>
            <div className="flex items-center justify-between gap-3 text-muted-foreground text-xs">
              <span className="truncate">
                {showOwner && claim.owner ? `${claim.owner.name} · ` : ""}
                {formatDate(claim.date, locale)}
              </span>
              <StageBadge status={claim.status} className="text-xs" />
            </div>
            {claim.costCentres.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {claim.costCentres.map((cc) => (
                  <CostCentreChip key={cc} name={cc} />
                ))}
              </div>
            )}
          </Link>
        </li>
      ))}
    </ul>
  );
}
