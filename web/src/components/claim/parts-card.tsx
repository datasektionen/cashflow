import { CircleCheck, Clock, Loader2, Stamp } from "lucide-react";
import { Amount, CostCentreChip } from "#/components/claims/badges";
import { Button } from "#/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import type { Claim } from "#/gen/cashflow/claim/v1/claim_pb";
import { formatDate } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";
import { useClaimAction } from "./use-claim-action";

/** How the amount is split over cost centres, who attested each part, and attest buttons where allowed. */
export function PartsCard({ claim }: { claim: Claim }) {
  const t = useT();
  const locale = useLocale();
  const s = claim.summary;
  const parts = claim.parts;
  const total = s?.amountOre ?? 0n;
  const ref = { kind: s?.kind ?? 0, number: s?.number ?? 0n };
  const { client, run, pending } = useClaimAction(ref.kind, ref.number);
  // Per-part buttons only when there is a choice to make; a single part is
  // attested from the next-step panel, so there is never a second button.
  const perPart = parts.length > 1;
  const canAttest = new Set(perPart ? claim.actions?.attestPartIds : []);
  const canUnattest = new Set(perPart ? claim.actions?.unattestPartIds : []);
  const setAttested = (partId: bigint, attested: boolean) =>
    run({
      key: `part-${partId}`,
      done: attested ? t.claim.done.attest : t.claim.done.unattest,
      call: () => client.setPartAttested({ claim: ref, partId, attested }),
    });
  return (
    <Card className="gap-0 pb-0">
      <CardHeader>
        <CardTitle>{t.claim.parts}</CardTitle>
      </CardHeader>
      <CardContent className="px-0">
        <ul className="divide-y">
          {parts.map((part) => (
            <li key={part.id.toString()} className="flex items-center justify-between gap-3 px-4 py-2">
              <div className="flex min-w-0 flex-col gap-0.5">
                <div className="flex flex-wrap items-center gap-2">
                  <CostCentreChip name={part.costCentre || "–"} />
                  <span className="truncate text-sm">
                    {[part.secondaryCostCentre, part.budgetLine].filter(Boolean).join(" › ")}
                  </span>
                </div>
                {part.attestedBy ? (
                  <span className="flex items-center gap-1.5 text-success-ink text-xs">
                    <CircleCheck className="size-3.5" />
                    {t.claim.attestedBy(part.attestedBy.name, formatDate(part.attestedAt, locale))}
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-muted-foreground text-xs">
                    <Clock className="size-3.5" />
                    {t.claim.notAttested}
                  </span>
                )}
              </div>
              <div className="flex shrink-0 flex-row-reverse items-center gap-2">
                <Amount ore={part.amountOre} />
                {canAttest.has(part.id) && (
                  <Button
                    size="xs"
                    variant="outline"
                    disabled={pending !== undefined}
                    onClick={() => setAttested(part.id, true)}
                  >
                    {pending === `part-${part.id}` ? <Loader2 className="animate-spin" /> : <Stamp />}
                    {t.claim.actions.attest}
                  </Button>
                )}
                {canUnattest.has(part.id) && (
                  <Button
                    size="xs"
                    variant="ghost"
                    className="text-muted-foreground"
                    disabled={pending !== undefined}
                    onClick={() => setAttested(part.id, false)}
                  >
                    {t.claim.actions.unattest}
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
        {parts.length > 1 && (
          <div className="flex justify-between border-t bg-muted/50 px-4 py-2 font-medium text-sm">
            <span>{t.claim.total}</span>
            <Amount ore={total} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
