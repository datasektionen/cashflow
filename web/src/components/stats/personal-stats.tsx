import { useQuery } from "@connectrpc/connect-query";
import { keepPreviousData } from "@tanstack/react-query";
import { Trophy } from "lucide-react";
import { useState } from "react";
import { Amount } from "#/components/claims/badges";
import { Card, CardContent } from "#/components/ui/card";
import { Skeleton } from "#/components/ui/skeleton";
import { Period } from "#/gen/cashflow/stats/v1/stats_pb";
import { getPersonalStats } from "#/gen/cashflow/stats/v1/stats-StatsService_connectquery";
import { useT } from "#/lib/i18n";
import { PeriodToggle } from "./period-toggle";

/**
 * One person's expenses and places on the leaderboards, for a period: the
 * caller's own without a username (Cashflow 3's personal stats).
 */
export function PersonalStats({ username }: { username?: string }) {
  const t = useT();
  const s = t.stats;
  const [period, setPeriod] = useState(Period.YEAR);
  const { data } = useQuery(getPersonalStats, { username, period }, { placeholderData: keepPreviousData });
  const place = (rank: number | undefined) => (rank ? s.place(rank, data?.people ?? 0) : s.noPlace);
  const tiles = [
    { label: s.measure.total, value: data && <Amount ore={data.totalOre} /> },
    { label: s.measure.count, value: data && s.expenses(data.count) },
    { label: s.byTotal, value: data && place(data.totalRank), trophy: data?.totalRank === 1 },
    { label: s.byCount, value: data && place(data.countRank), trophy: data?.countRank === 1 },
  ];
  return (
    <Card size="sm">
      <CardContent className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <PeriodToggle value={period} onChange={setPeriod} />
        <dl className="flex flex-1 flex-wrap gap-x-6 gap-y-2">
          {tiles.map(({ label, value, trophy }) => (
            <div key={label} className="flex flex-col leading-tight">
              <dt className="text-muted-foreground text-xs">{label}</dt>
              <dd className="flex items-center gap-1 font-medium">
                {value ?? <Skeleton className="h-5 w-20" />}
                {trophy && <Trophy className="size-3.5 text-[oklch(0.7_0.15_80)]" aria-hidden />}
              </dd>
            </div>
          ))}
        </dl>
      </CardContent>
    </Card>
  );
}
