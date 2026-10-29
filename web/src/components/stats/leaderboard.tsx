import { useQuery } from "@connectrpc/connect-query";
import { keepPreviousData } from "@tanstack/react-query";
import { Amount } from "#/components/claims/badges";
import { UserAvatar } from "#/components/layout/user-avatar";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import { Skeleton } from "#/components/ui/skeleton";
import { type Period, Ranking } from "#/gen/cashflow/stats/v1/stats_pb";
import { getLeaderboard } from "#/gen/cashflow/stats/v1/stats-StatsService_connectquery";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { useT } from "#/lib/i18n";
import { cn } from "#/lib/utils";

// Gold, silver and bronze for the podium; everyone else gets a plain number.
const medal = [
  "bg-[oklch(0.88_0.12_90)] text-[oklch(0.35_0.08_80)]",
  "bg-[oklch(0.9_0.01_250)] text-[oklch(0.35_0.02_250)]",
  "bg-[oklch(0.85_0.08_55)] text-[oklch(0.38_0.08_50)]",
];

/** The top ten by sum or by number, with the caller marked when they are on it. */
export function Leaderboard({ ranking, period }: { ranking: Ranking; period: Period }) {
  const t = useT();
  const s = t.stats;
  const me = useQuery(getMe, {}).data?.user?.username;
  const { data } = useQuery(getLeaderboard, { ranking, period }, { placeholderData: keepPreviousData });
  const byCount = ranking === Ranking.COUNT;

  return (
    <Card size="sm" className="gap-1">
      <CardHeader>
        <CardTitle>{byCount ? s.byCount : s.byTotal}</CardTitle>
      </CardHeader>
      <CardContent className="px-2">
        {!data ? (
          <div className="flex flex-col gap-1.5 px-2">
            {Array.from({ length: 6 }, (_, i) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: static placeholders
              <Skeleton key={i} className="h-7" />
            ))}
          </div>
        ) : data.entries.length === 0 ? (
          <p className="px-2 py-6 text-center text-muted-foreground text-sm">{s.emptyLeaderboard}</p>
        ) : (
          <ol className="flex flex-col">
            {data.entries.slice(0, 10).map((e) => {
              const mine = e.person?.username === me;
              return (
                <li
                  key={e.person?.username}
                  className={cn("flex h-8 items-center gap-2.5 rounded-md px-2 text-sm", mine && "bg-primary/10")}
                >
                  <span
                    className={cn(
                      "flex size-6 shrink-0 items-center justify-center rounded-full font-medium text-xs tabular-nums",
                      medal[e.rank - 1] ?? "text-muted-foreground",
                    )}
                  >
                    {e.rank}
                  </span>
                  <UserAvatar
                    name={e.person?.name ?? ""}
                    username={e.person?.username}
                    size="sm"
                    className="bg-secondary"
                  />
                  <span className="min-w-0 flex-1 truncate">
                    {e.person?.name}
                    {mine && <span className="text-muted-foreground"> ({s.you})</span>}
                  </span>
                  <span className="shrink-0 font-medium">
                    {byCount ? s.expenses(e.count) : <Amount ore={e.totalOre} />}
                  </span>
                </li>
              );
            })}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
