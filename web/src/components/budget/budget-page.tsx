import { useQuery } from "@connectrpc/connect-query";
import { keepPreviousData } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, PiggyBank, SearchIcon, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { Amount } from "#/components/claims/badges";
import { StateCard } from "#/components/layout/states";
import { Button } from "#/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import { Input } from "#/components/ui/input";
import { Skeleton } from "#/components/ui/skeleton";
import { Toggle } from "#/components/ui/toggle";
import type { BudgetLine, CostCentre } from "#/gen/cashflow/budget/v1/budget_pb";
import { getBudget } from "#/gen/cashflow/budget/v1/budget-BudgetService_connectquery";
import { useT } from "#/lib/i18n";
import { cn } from "#/lib/utils";
import { UsageBar } from "./usage-bar";

export type BudgetSearch = { cc?: number; year?: number; blown?: boolean };

const TYPE_ORDER = ["committee", "partition", "project", "projectX", "other"];

const sum = (lines: BudgetLine[], pick: (l: BudgetLine) => bigint) => lines.reduce((s, l) => s + pick(l), 0n);
const linesOf = (cc: CostCentre) => cc.secondary.flatMap((s) => s.lines);

/**
 * GOrdian's budget beside what has been claimed against it: cost centres on
 * the left, grouped by kind, and the chosen one's budget lines on the right.
 * Everything fits one screen; the two columns scroll on their own.
 */
export function BudgetPage({
  search,
  onSearch,
}: {
  search: BudgetSearch;
  onSearch: (change: Partial<BudgetSearch>) => void;
}) {
  const t = useT();
  const b = t.budget;
  const thisYear = new Date().getFullYear();
  const year = search.year ?? thisYear;
  const budget = useQuery(getBudget, { year }, { placeholderData: keepPreviousData });
  const [query, setQuery] = useState("");

  if (budget.isError) {
    return <StateCard icon={<TriangleAlert />} title={t.errors.title} description={b.unavailable} />;
  }
  const all = budget.data?.costCentres ?? [];
  const visible = all.filter(
    (cc) => (!search.blown || cc.containsBlown) && cc.name.toLowerCase().includes(query.trim().toLowerCase()),
  );
  const groups = TYPE_ORDER.map((type) => ({ type, items: visible.filter((cc) => cc.type === type) })).filter(
    (g) => g.items.length > 0,
  );
  const selected = all.find((cc) => cc.id === search.cc);

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] items-start gap-4 lg:grid-cols-[18rem_minmax(0,1fr)]">
      <Card size="sm" className="gap-2 lg:sticky lg:top-4 lg:max-h-[calc(100dvh-7.5rem)]">
        <CardHeader className="flex flex-col gap-2">
          <div className="relative w-full">
            <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={b.search}
              aria-label={b.search}
              className="pl-8"
            />
          </div>
          <div className="flex w-full items-center justify-between gap-2">
            <Toggle
              variant="outline"
              size="sm"
              pressed={Boolean(search.blown)}
              onPressedChange={(pressed) => onSearch({ blown: pressed || undefined })}
            >
              <TriangleAlert /> {b.onlyBlown}
            </Toggle>
            <div className="flex items-center">
              <Button
                variant="ghost"
                size="icon-xs"
                aria-label={t.stats.previousYear}
                onClick={() => onSearch({ year: year - 1 })}
              >
                <ChevronLeft />
              </Button>
              <span className="w-10 text-center font-medium text-sm tabular-nums">{year}</span>
              <Button
                variant="ghost"
                size="icon-xs"
                aria-label={t.stats.nextYear}
                disabled={year >= thisYear}
                onClick={() => onSearch({ year: year + 1 === thisYear ? undefined : year + 1 })}
              >
                <ChevronRight />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="min-h-0 overflow-y-auto px-2">
          {!budget.data ? (
            <div className="flex flex-col gap-1.5 px-2">
              {Array.from({ length: 10 }, (_, i) => (
                // biome-ignore lint/suspicious/noArrayIndexKey: static placeholders
                <Skeleton key={i} className="h-8" />
              ))}
            </div>
          ) : groups.length === 0 ? (
            <p className="px-2 py-4 text-muted-foreground text-sm">{b.noneMatch}</p>
          ) : (
            groups.map((group) => (
              <section key={group.type} aria-label={b.types[group.type] ?? group.type} className="mb-2">
                <h3 className="px-2 pt-1 pb-0.5 font-medium text-muted-foreground text-xs">
                  {b.types[group.type] ?? group.type}
                </h3>
                <ul>
                  {group.items.map((cc) => {
                    const lines = linesOf(cc);
                    return (
                      <li key={cc.id}>
                        <button
                          type="button"
                          aria-current={cc.id === search.cc || undefined}
                          onClick={() => onSearch({ cc: cc.id })}
                          className={cn(
                            "flex w-full flex-col gap-1 rounded-md px-2 py-1.5 text-left text-sm outline-none hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring",
                            cc.id === search.cc && "bg-accent hover:bg-accent",
                          )}
                        >
                          <span className="flex items-center gap-1.5">
                            <span className="min-w-0 flex-1 truncate">{cc.name}</span>
                            {cc.containsBlown && (
                              <TriangleAlert className="size-3.5 shrink-0 text-destructive-ink" aria-label={b.blown} />
                            )}
                          </span>
                          <UsageBar
                            budget={sum(lines, (l) => l.expenseOre)}
                            used={sum(lines, (l) => l.usedOre)}
                            attested={sum(lines, (l) => l.attestedOre)}
                            paid={sum(lines, (l) => l.paidOre)}
                            className="h-1"
                          />
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </section>
            ))
          )}
        </CardContent>
      </Card>

      {selected ? (
        <CostCentreDetail cc={selected} year={year} />
      ) : (
        <StateCard icon={<PiggyBank />} title={b.title} description={b.choose} className="hidden lg:flex" />
      )}
    </div>
  );
}

function CostCentreDetail({ cc, year }: { cc: CostCentre; year: number }) {
  const t = useT();
  const b = t.budget;
  const c = b.columns;
  const lines = linesOf(cc);
  const total = (pick: (l: BudgetLine) => bigint) => sum(lines, pick);
  const cols = "grid grid-cols-[minmax(0,1fr)_repeat(5,6.5rem)] items-center gap-x-3";

  return (
    <Card size="sm" className="gap-2 lg:max-h-[calc(100dvh-7.5rem)]">
      <CardHeader className="flex flex-wrap items-baseline gap-x-3">
        <CardTitle className="font-display text-lg">{cc.name}</CardTitle>
        <span className="text-muted-foreground text-sm">
          {b.types[cc.type] ?? cc.type} · {year}
        </span>
      </CardHeader>
      <CardContent className="min-h-0 overflow-auto">
        <div className="min-w-[44rem] text-sm">
          <div className={cn(cols, "sticky top-0 z-10 border-b bg-card pb-1.5 text-muted-foreground text-xs")}>
            <span>{c.line}</span>
            {[c.budget, c.used, c.attested, c.paid, c.left].map((label) => (
              <span key={label} className="text-right">
                {label}
              </span>
            ))}
          </div>
          {cc.secondary.map((scc) => (
            <section key={scc.id} aria-label={scc.name}>
              <h3 className="pt-3 pb-1 font-medium text-xs">{scc.name}</h3>
              <ul>
                {scc.lines.map((line) => (
                  <li key={line.id} className={cn(cols, "border-b border-dashed py-1 last:border-0")}>
                    <div className="flex min-w-0 flex-col gap-0.5">
                      <span className="flex items-center gap-1.5">
                        <Link
                          to="/claims"
                          search={{
                            cc: cc.name,
                            scc: scc.name,
                            line: line.name,
                            from: `${year}-01-01`,
                            to: `${year}-12-31`,
                          }}
                          title={b.showClaims(line.name)}
                          className="truncate underline-offset-2 hover:underline"
                        >
                          {line.name}
                        </Link>
                        {line.blown && (
                          <span
                            className="inline-flex shrink-0 items-center gap-1 font-medium text-destructive-ink text-xs"
                            title={b.blownHint}
                          >
                            <TriangleAlert className="size-3" /> {b.blown}
                          </span>
                        )}
                      </span>
                      <UsageBar
                        budget={line.expenseOre}
                        used={line.usedOre}
                        attested={line.attestedOre}
                        paid={line.paidOre}
                        className="h-1"
                      />
                    </div>
                    {line.expenseOre > 0n ? (
                      <Amount ore={line.expenseOre} className="text-right" />
                    ) : (
                      <span className="text-right text-muted-foreground text-xs">{b.noBudget}</span>
                    )}
                    <MaybeAmount ore={line.usedOre} />
                    <MaybeAmount ore={line.attestedOre} muted />
                    <MaybeAmount ore={line.paidOre} muted />
                    {line.expenseOre > 0n ? (
                      <Amount
                        ore={line.expenseOre - line.usedOre}
                        className={cn("text-right font-medium", line.blown && "text-destructive-ink")}
                      />
                    ) : (
                      <span />
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}
          <div className={cn(cols, "mt-2 border-t pt-2 font-medium")}>
            <span>{b.total}</span>
            <Amount ore={total((l) => l.expenseOre)} className="text-right" />
            <Amount ore={total((l) => l.usedOre)} className="text-right" />
            <Amount ore={total((l) => l.attestedOre)} className="text-right" />
            <Amount ore={total((l) => l.paidOre)} className="text-right" />
            <span />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/** Nothing claimed shows as a dash, so the amounts that matter stand out. */
function MaybeAmount({ ore, muted = false }: { ore: bigint; muted?: boolean }) {
  if (ore === 0n) return <span className="text-right text-muted-foreground">–</span>;
  return <Amount ore={ore} className={cn("text-right", muted && "text-muted-foreground")} />;
}
