import { useQuery } from "@connectrpc/connect-query";
import { Link } from "@tanstack/react-router";
import { CircleCheckBig } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import { Queue } from "#/gen/cashflow/claim/v1/claim_pb";
import { getWorkOverview } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { useT } from "#/lib/i18n";
import { navigation } from "#/lib/navigation";

const SHOWN = 4;
const row = "flex items-center gap-2 rounded px-1 text-sm leading-6 hover:bg-muted";
// Queue pages all take the claims list's search params, cost centre included.
const queuePath = {
  [Queue.UNSPECIFIED]: "/attest",
  [Queue.ATTEST]: "/attest",
  [Queue.CONFIRM]: "/confirm",
  [Queue.ACCOUNT]: "/account",
  [Queue.PAY]: "/pay",
} as const;

/**
 * Cashflow 3's admin overview, on the home page: each of the caller's queues
 * with what waits in it by cost centre (or, to pay, by person), every count a
 * link straight into the filtered queue. Nothing for those without queues.
 */
export function WorkOverview() {
  const t = useT();
  const { data } = useQuery(getWorkOverview, {});
  if (!data || data.queues.length === 0) return null;
  const items = navigation.flatMap((g) => g.items);

  return (
    <Card size="sm" className="gap-2">
      <CardHeader>
        <CardTitle>{t.work.title}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-x-6 gap-y-2 sm:grid-cols-2 xl:grid-cols-4">
        {data.queues.map((q) => {
          const item = items.find((i) => i.queue === q.queue);
          if (!item) return null;
          const Icon = item.icon;
          const isPay = q.queue === Queue.PAY;
          return (
            <section key={q.queue} aria-label={item.label(t)} className="flex min-w-0 flex-col gap-1">
              <Link
                to={item.to}
                className="flex items-center gap-1.5 font-medium text-sm underline-offset-2 hover:underline"
              >
                <Icon className="size-4 text-primary" /> {item.label(t)}
                {q.total > 0 && <span className="ml-auto text-xs">{t.work.total(q.total)}</span>}
              </Link>
              {q.total === 0 ? (
                <span className="flex items-center gap-1.5 text-muted-foreground text-xs">
                  <CircleCheckBig className="size-3.5 text-primary" /> {t.work.allDone}
                </span>
              ) : (
                <ul className="flex flex-col">
                  {q.groups.slice(0, SHOWN).map((g) => (
                    <li key={g.key}>
                      {isPay ? (
                        <Link to="/users/$username" params={{ username: g.key }} className={row}>
                          <span className="min-w-0 flex-1 truncate text-muted-foreground">{g.label}</span>
                          <span className="font-medium tabular-nums">{g.count}</span>
                        </Link>
                      ) : (
                        <Link to={queuePath[q.queue]} search={{ cc: g.key }} className={row}>
                          <span className="min-w-0 flex-1 truncate text-muted-foreground">{g.label}</span>
                          <span className="font-medium tabular-nums">{g.count}</span>
                        </Link>
                      )}
                    </li>
                  ))}
                  {q.groups.length > SHOWN && (
                    <li className="px-1 text-muted-foreground text-xs">+{q.groups.length - SHOWN}</li>
                  )}
                </ul>
              )}
            </section>
          );
        })}
      </CardContent>
    </Card>
  );
}
