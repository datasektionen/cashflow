import { cn } from "#/lib/utils";

/**
 * How much of a budget is used, in one hue from light to dark: claimed,
 * attested, paid. Overspent turns the bar red; the text beside it says so
 * too, so the colour is never the only sign.
 */
export function UsageBar({
  budget,
  used,
  attested = 0n,
  paid = 0n,
  className,
}: {
  budget: bigint;
  used: bigint;
  attested?: bigint;
  paid?: bigint;
  className?: string;
}) {
  const pct = (v: bigint) => (budget > 0n ? Math.min(100, (Number(v) / Number(budget)) * 100) : 0);
  const over = budget > 0n && used > budget;
  return (
    <div aria-hidden className={cn("relative h-1.5 overflow-hidden rounded-full bg-muted", className)}>
      {over ? (
        <div className="absolute inset-0 bg-destructive" />
      ) : (
        <>
          <div className="absolute inset-y-0 left-0 rounded-full bg-primary/30" style={{ width: `${pct(used)}%` }} />
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-primary/60"
            style={{ width: `${pct(attested)}%` }}
          />
          <div className="absolute inset-y-0 left-0 rounded-full bg-primary" style={{ width: `${pct(paid)}%` }} />
        </>
      )}
    </div>
  );
}
