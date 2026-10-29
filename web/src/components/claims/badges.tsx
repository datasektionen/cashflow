import { FileText, Flag, Receipt } from "lucide-react";
import type { ComponentProps } from "react";
import { ClaimKind, type Status } from "#/gen/cashflow/claim/v1/claim_pb";
import { costCentreHue, type StageSlug, stageSlug } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";
import { formatOre } from "#/lib/money";
import { cn } from "#/lib/utils";

/** An amount in öre as "1 234,50 kr", in tabular figures. */
export function Amount({ ore, className }: { ore: bigint; className?: string }) {
  const t = useT();
  const locale = useLocale();
  return (
    <span className={cn("whitespace-nowrap", className)}>
      <span className="amount">{formatOre(ore, locale)}</span>{" "}
      <span className="text-[0.85em] text-muted-foreground">{t.money.currency}</span>
    </span>
  );
}

export function KindIcon({ kind, className }: { kind: ClaimKind; className?: string }) {
  const Icon = kind === ClaimKind.INVOICE ? FileText : Receipt;
  return <Icon aria-hidden className={cn("size-4 shrink-0 text-muted-foreground", className)} />;
}

/** A cost centre with its own stable colour; clickable when given onClick. */
export function CostCentreChip({ name, className, ...props }: { name: string } & ComponentProps<"button">) {
  const hue = costCentreHue(name);
  const Tag = props.onClick ? "button" : "span";
  return (
    <Tag
      {...(props.onClick ? { type: "button" as const } : {})}
      {...props}
      style={{ "--chip-hue": hue } as React.CSSProperties}
      className={cn(
        "inline-flex max-w-full items-center truncate rounded-md px-1.5 py-0.5 font-medium text-xs",
        "bg-[oklch(0.95_0.035_var(--chip-hue))] text-[oklch(0.4_0.09_var(--chip-hue))]",
        "dark:bg-[oklch(0.3_0.05_var(--chip-hue))] dark:text-[oklch(0.86_0.07_var(--chip-hue))]",
        props.onClick &&
          "cursor-pointer outline-none transition hover:ring-1 hover:ring-current/30 focus-visible:ring-2 focus-visible:ring-ring",
        className,
      )}
    >
      {name}
    </Tag>
  );
}

const stageDot: Record<StageSlug, string> = {
  submitted: "bg-muted-foreground/40",
  attested: "bg-info",
  confirmed: "bg-[oklch(0.65_0.13_190)]",
  paid: "bg-success",
  accounted: "bg-primary",
};

/** Where a claim is, as a coloured dot and a word; flagged claims say so first. */
export function StageBadge({ status, className }: { status: Status | undefined; className?: string }) {
  const t = useT();
  if (!status) return null;
  const stage = stageSlug[status.stage];
  return (
    <span className={cn("inline-flex items-center gap-2 whitespace-nowrap text-sm", className)}>
      {status.flagged ? (
        <span className="inline-flex items-center gap-1 font-medium text-destructive-ink">
          <Flag aria-hidden className="size-3.5" /> {t.claims.flagged}
        </span>
      ) : (
        <>
          <span aria-hidden className={cn("size-2 rounded-full", stageDot[stage])} />
          {t.claims.stage[stage]}
        </>
      )}
    </span>
  );
}
