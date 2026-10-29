import { CircleCheck, Clock } from "lucide-react";
import { Amount, CostCentreChip } from "#/components/claims/badges";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import type { Part } from "#/gen/cashflow/claim/v1/claim_pb";
import { formatDate } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";

/** How the amount is split over cost centres, and who attested each part. */
export function PartsCard({ parts, total }: { parts: Part[]; total: bigint }) {
  const t = useT();
  const locale = useLocale();
  return (
    <Card className="gap-0 pb-0">
      <CardHeader>
        <CardTitle>{t.claim.parts}</CardTitle>
      </CardHeader>
      <CardContent className="px-0">
        <ul className="divide-y">
          {parts.map((part) => (
            <li key={part.id.toString()} className="flex items-start justify-between gap-4 px-6 py-3">
              <div className="flex min-w-0 flex-col gap-1">
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
              <Amount ore={part.amountOre} className="pt-0.5" />
            </li>
          ))}
        </ul>
        {parts.length > 1 && (
          <div className="flex justify-between border-t bg-muted/50 px-6 py-3 font-medium text-sm">
            <span>{t.claim.total}</span>
            <Amount ore={total} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
