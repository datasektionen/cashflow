import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Page } from "#/components/layout/page";
import { Leaderboard } from "#/components/stats/leaderboard";
import { PeriodToggle } from "#/components/stats/period-toggle";
import { YearChart } from "#/components/stats/year-chart";
import { Period, Ranking } from "#/gen/cashflow/stats/v1/stats_pb";
import { useT } from "#/lib/i18n";

export const Route = createFileRoute("/_app/stats")({
  component: StatsPage,
});

/** Cashflow 3's statistics: the year month by month, and who lays out the most. */
function StatsPage() {
  const t = useT();
  const [period, setPeriod] = useState(Period.YEAR);
  return (
    <Page title={t.stats.title}>
      <div className="flex flex-col gap-4">
        <YearChart />
        <section aria-labelledby="leaderboard" className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <h2 id="leaderboard" className="font-display font-semibold text-lg">
              {t.stats.leaderboard}
            </h2>
            <p className="text-muted-foreground text-xs">{t.stats.leaderboardHelp}</p>
            <div className="ml-auto">
              <PeriodToggle value={period} onChange={setPeriod} />
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Leaderboard ranking={Ranking.TOTAL} period={period} />
            <Leaderboard ranking={Ranking.COUNT} period={period} />
          </div>
        </section>
      </div>
    </Page>
  );
}
