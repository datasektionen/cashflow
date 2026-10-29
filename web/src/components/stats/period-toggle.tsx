import { ToggleGroup, ToggleGroupItem } from "#/components/ui/toggle-group";
import { Period } from "#/gen/cashflow/stats/v1/stats_pb";
import { useT } from "#/lib/i18n";

const PERIODS = [
  [Period.ALL_TIME, "all"],
  [Period.YEAR, "year"],
  [Period.MONTH, "month"],
] as const;

/** All time, this year or this month: the leaderboards' periods. */
export function PeriodToggle({ value, onChange }: { value: Period; onChange: (period: Period) => void }) {
  const t = useT();
  return (
    <ToggleGroup
      variant="outline"
      size="sm"
      value={[String(value)]}
      onValueChange={(next: string[]) => {
        if (next[0]) onChange(Number(next[0]) as Period);
      }}
    >
      {PERIODS.map(([period, slug]) => (
        <ToggleGroupItem key={slug} value={String(period)} className="px-2.5">
          {t.stats.period[slug]}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}
