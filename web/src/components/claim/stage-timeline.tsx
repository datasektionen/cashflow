import { Check } from "lucide-react";
import type { Claim } from "#/gen/cashflow/claim/v1/claim_pb";
import { formatDate, type StageSlug, stepsFor } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";
import { cn } from "#/lib/utils";

type Step = { stage: StageSlug; done: boolean; detail?: string };

/** What happened when, per step; a step can be done out of order (confirming before attesting). */
function steps(claim: Claim, t: ReturnType<typeof useT>, locale: ReturnType<typeof useLocale>): Step[] {
  const s = claim.summary;
  if (!s?.status) return [];
  const lastAttest = claim.parts
    .map((p) => p.attestedAt)
    .sort()
    .at(-1);
  const detail: Record<StageSlug, { done: boolean; detail?: string }> = {
    submitted: { done: true, detail: formatDate(s.createdDate, locale) },
    attested: { done: s.status.attested, detail: formatDate(lastAttest ?? "", locale) },
    confirmed: {
      done: s.status.confirmed,
      detail: claim.confirmedBy
        ? `${formatDate(claim.confirmedAt, locale)} ${t.claim.confirmedBy(claim.confirmedBy.name)}`
        : undefined,
    },
    paid: {
      done: s.status.paid,
      detail: claim.payment
        ? `${formatDate(claim.payment.date, locale)} · ${claim.payment.tag}`
        : formatDate(claim.paidAt, locale),
    },
    accounted: { done: Boolean(s.status.verification), detail: s.status.verification },
  };
  return stepsFor(s.kind).map((stage) => ({ stage, ...detail[stage] }));
}

/**
 * The workflow as steps: done ones ticked, the next one pulsing. Vertical on
 * phones, a row from small screens up.
 */
export function StageTimeline({ claim }: { claim: Claim }) {
  const t = useT();
  const locale = useLocale();
  const list = steps(claim, t, locale);
  const next = list.findIndex((step) => !step.done);

  return (
    <ol className="flex flex-col sm:flex-row">
      {list.map((step, i) => {
        const last = i === list.length - 1;
        return (
          <li
            key={step.stage}
            className="relative flex flex-1 gap-3 pb-3 last:pb-0 sm:flex-col sm:gap-1 sm:pr-2 sm:pb-0"
          >
            <div className="flex flex-col items-center sm:flex-row">
              <span
                className={cn(
                  "flex size-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors",
                  step.done && "border-primary bg-primary text-primary-foreground",
                  !step.done && i === next && "border-primary bg-card",
                  !step.done && i !== next && "border-border bg-card",
                )}
              >
                {step.done ? (
                  <Check className="size-3" strokeWidth={3} />
                ) : (
                  i === next && <span className="size-1.5 animate-pulse rounded-full bg-primary" />
                )}
              </span>
              {!last && (
                <span
                  aria-hidden
                  className={cn(
                    "mt-1 w-0.5 flex-1 rounded sm:mt-0 sm:ml-2 sm:h-0.5 sm:w-auto",
                    step.done ? "bg-primary/60" : "bg-border",
                  )}
                />
              )}
            </div>
            <div className="flex flex-col gap-0.5 pt-0.5 sm:pt-0">
              <span className={cn("font-medium text-xs", !step.done && "text-muted-foreground")}>
                {t.claim.step[step.stage]}
              </span>
              <span className="text-muted-foreground text-xs">
                {step.done ? step.detail : i === next ? t.claim.stepWaiting : ""}
              </span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
