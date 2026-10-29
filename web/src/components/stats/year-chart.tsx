import { useQuery } from "@connectrpc/connect-query";
import { keepPreviousData } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import { Button } from "#/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "#/components/ui/toggle-group";
import type { Month } from "#/gen/cashflow/stats/v1/stats_pb";
import { getYear } from "#/gen/cashflow/stats/v1/stats-StatsService_connectquery";
import { intlLocale, useLocale, useT } from "#/lib/i18n";
import { formatOre } from "#/lib/money";
import { cn } from "#/lib/utils";

type Kind = "expense" | "invoice";
type Measure = "total" | "count";

const W = 720;
const H = 200;
const PAD = { top: 8, right: 4, bottom: 22, left: 60 };

/** A round step for about four gridlines. */
function niceStep(max: number) {
  const raw = Math.max(max, 1) / 4;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  return ([1, 2, 2.5, 5, 10].find((m) => m * magnitude >= raw) ?? 10) * magnitude;
}

/** A bar with a rounded top and a square foot on the baseline. */
function barPath(x: number, y: number, w: number, h: number) {
  const r = Math.min(4, w / 2, h);
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`;
}

/**
 * Expenses or invoices per month for a year, as a sum or a number. One
 * series, so one colour and no legend; hovering a month shows its value, and
 * a table holds the same numbers for screen readers.
 */
export function YearChart() {
  const t = useT();
  const s = t.stats;
  const locale = useLocale();
  const thisYear = new Date().getFullYear();
  const [year, setYear] = useState(thisYear);
  const [kind, setKind] = useState<Kind>("expense");
  const [measure, setMeasure] = useState<Measure>("total");
  const [hover, setHover] = useState<number>();
  const { data } = useQuery(getYear, { year }, { placeholderData: keepPreviousData });

  const months = data?.months ?? [];
  const value = (m: Month) =>
    kind === "expense"
      ? measure === "total"
        ? Number(m.expenseTotalOre) / 100
        : m.expenseCount
      : measure === "total"
        ? Number(m.invoiceTotalOre) / 100
        : m.invoiceCount;
  const ore = (m: Month) => (kind === "expense" ? m.expenseTotalOre : m.invoiceTotalOre);
  const count = (m: Month) => (kind === "expense" ? m.expenseCount : m.invoiceCount);
  const shown = (m: Month) =>
    measure === "total" ? `${formatOre(ore(m), locale)} ${t.money.currency}` : String(count(m));

  const step = niceStep(Math.max(0, ...months.map(value)));
  const top = step * Math.ceil(Math.max(0, ...months.map(value), 1) / step);
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const slot = plotW / 12;
  const barW = Math.min(28, slot * 0.6);
  const yOf = (v: number) => PAD.top + plotH - (v / top) * plotH;
  const monthName = (m: number, style: "short" | "long") =>
    new Intl.DateTimeFormat(intlLocale[locale], { month: style }).format(new Date(2000, m - 1, 15));
  const axis = new Intl.NumberFormat(intlLocale[locale], { maximumFractionDigits: 0 });
  const ticks = Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step);
  const hovered = hover !== undefined ? months[hover] : undefined;
  const hoveredValue = hovered ? value(hovered) : 0;

  return (
    <Card size="sm">
      <CardHeader className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon-sm" aria-label={s.previousYear} onClick={() => setYear((y) => y - 1)}>
            <ChevronLeft />
          </Button>
          <CardTitle className="w-12 text-center tabular-nums">{year}</CardTitle>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={s.nextYear}
            disabled={year >= thisYear}
            onClick={() => setYear((y) => y + 1)}
          >
            <ChevronRight />
          </Button>
        </div>
        <div className="ml-auto flex flex-wrap gap-2">
          <ToggleGroup
            variant="outline"
            size="sm"
            value={[kind]}
            onValueChange={(v: string[]) => v[0] && setKind(v[0] as Kind)}
          >
            {(["expense", "invoice"] as const).map((k) => (
              <ToggleGroupItem key={k} value={k} className="px-2.5">
                {s.kind[k]}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
          <ToggleGroup
            variant="outline"
            size="sm"
            value={[measure]}
            onValueChange={(v: string[]) => v[0] && setMeasure(v[0] as Measure)}
          >
            {(["total", "count"] as const).map((m) => (
              <ToggleGroupItem key={m} value={m} className="px-2.5">
                {s.measure[m]}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <svg viewBox={`0 0 ${W} ${H}`} className="h-auto w-full" aria-hidden onMouseLeave={() => setHover(undefined)}>
            {ticks.map((tick) => (
              <g key={tick}>
                <line
                  x1={PAD.left}
                  x2={W - PAD.right}
                  y1={yOf(tick)}
                  y2={yOf(tick)}
                  className={tick === 0 ? "stroke-border" : "stroke-border/60"}
                  strokeDasharray={tick === 0 ? undefined : "2 4"}
                />
                <text
                  x={PAD.left - 8}
                  y={yOf(tick)}
                  dy="0.32em"
                  textAnchor="end"
                  className="fill-muted-foreground text-[11px] tabular-nums"
                >
                  {axis.format(tick)}
                </text>
              </g>
            ))}
            {months.map((m, i) => {
              const v = value(m);
              const x = PAD.left + i * slot + (slot - barW) / 2;
              return (
                <g key={m.month}>
                  {v > 0 && (
                    <path
                      d={barPath(x, yOf(v), barW, PAD.top + plotH - yOf(v))}
                      className={cn(
                        "fill-chart-1 transition-opacity",
                        hover !== undefined && hover !== i && hoveredValue > 0 && "opacity-40",
                      )}
                    />
                  )}
                  <text
                    x={x + barW / 2}
                    y={H - 6}
                    textAnchor="middle"
                    className={cn("fill-muted-foreground text-[11px]", hover === i && "fill-foreground")}
                  >
                    {monthName(m.month, "short")}
                  </text>
                  {/* The whole column is the hover target, not just the bar. */}
                  {/* biome-ignore lint/a11y/noStaticElementInteractions: a mouse-only extra; the table below holds the same numbers */}
                  <rect
                    x={PAD.left + i * slot}
                    y={PAD.top}
                    width={slot}
                    height={plotH}
                    fill="transparent"
                    onMouseEnter={() => setHover(i)}
                  />
                </g>
              );
            })}
          </svg>
          {hovered && hover !== undefined && (
            <div
              className="pointer-events-none absolute top-0 z-10 -translate-x-1/2 rounded-md border bg-popover px-2.5 py-1.5 text-xs shadow-md"
              style={{ left: `${((PAD.left + (hover + 0.5) * slot) / W) * 100}%` }}
            >
              <div className="text-muted-foreground">
                {monthName(hovered.month, "long")} {year}
              </div>
              <div className="font-medium tabular-nums">{shown(hovered)}</div>
              {measure === "total" && kind === "expense" && (
                <div className="text-muted-foreground">{s.expenses(count(hovered))}</div>
              )}
            </div>
          )}
        </div>
        <table className="sr-only">
          <caption>{s.tableCaption(s.kind[kind], year)}</caption>
          <thead>
            <tr>
              <th scope="col">{s.month}</th>
              <th scope="col">{s.measure[measure]}</th>
            </tr>
          </thead>
          <tbody>
            {months.map((m) => (
              <tr key={m.month}>
                <th scope="row">{monthName(m.month, "long")}</th>
                <td>{shown(m)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
