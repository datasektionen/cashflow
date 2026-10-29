import { useQuery } from "@connectrpc/connect-query";
import { useDebouncedValue } from "@tanstack/react-pacer";
import { keepPreviousData } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { SearchIcon } from "lucide-react";
import { useState } from "react";
import { Page } from "#/components/layout/page";
import { UserAvatar } from "#/components/layout/user-avatar";
import { Card } from "#/components/ui/card";
import { Input } from "#/components/ui/input";
import { Skeleton } from "#/components/ui/skeleton";
import { listUsers } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { useT } from "#/lib/i18n";

export const Route = createFileRoute("/_app/users/")({
  component: UsersPage,
});

/** Everyone in Cashflow, searchable; for payers and admins. */
function UsersPage() {
  const t = useT();
  const [query, setQuery] = useState("");
  const [debounced] = useDebouncedValue(query.trim(), { wait: 200 });
  const { data } = useQuery(listUsers, { query: debounced }, { placeholderData: keepPreviousData });

  return (
    <Page title={t.users.title}>
      <div className="flex max-w-2xl flex-col gap-3">
        <div className="relative">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t.users.search}
            aria-label={t.users.search}
            className="pl-8"
          />
        </div>
        <Card className="gap-0 py-0">
          {!data ? (
            <div className="flex flex-col gap-2 p-3">
              {Array.from({ length: 6 }, (_, i) => (
                // biome-ignore lint/suspicious/noArrayIndexKey: static placeholders
                <Skeleton key={i} className="h-8" />
              ))}
            </div>
          ) : data.users.length === 0 ? (
            <p className="p-4 text-muted-foreground text-sm">{t.users.empty}</p>
          ) : (
            <ul className="divide-y">
              {data.users.map((u) => (
                <li key={u.username}>
                  <Link
                    to="/users/$username"
                    params={{ username: u.username }}
                    className="flex items-center gap-3 px-3 py-1.5 text-sm outline-none hover:bg-muted/60 focus-visible:bg-accent"
                  >
                    <UserAvatar name={u.name} username={u.username} size="sm" className="bg-secondary" />
                    <span className="min-w-0 flex-1 truncate font-medium">{u.name || u.username}</span>
                    <span className="truncate text-muted-foreground text-xs">{u.username}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </Page>
  );
}
