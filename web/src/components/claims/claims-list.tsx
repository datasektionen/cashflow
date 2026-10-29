import { useQuery } from "@connectrpc/connect-query";
import { useHotkey } from "@tanstack/react-hotkeys";
import { useDebouncedCallback } from "@tanstack/react-pacer";
import { keepPreviousData } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, SearchIcon, TriangleAlert, X } from "lucide-react";
import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { StateCard } from "#/components/layout/states";
import { Button } from "#/components/ui/button";
import { Card } from "#/components/ui/card";
import { Input } from "#/components/ui/input";
import { Kbd } from "#/components/ui/kbd";
import { Skeleton } from "#/components/ui/skeleton";
import { ToggleGroup, ToggleGroupItem } from "#/components/ui/toggle-group";
import { listClaims } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { useIsMobile } from "#/hooks/use-mobile";
import { claimLink, type KindSlug } from "#/lib/claims";
import { useT } from "#/lib/i18n";
import { ClaimCards } from "./claim-cards";
import { type ClaimScope, type ClaimSearch, effectiveSort, listRequest, PAGE_SIZE } from "./claim-search";
import { ClaimsTable } from "./claims-table";

type Props = {
  scope: ClaimScope;
  search: ClaimSearch;
  /** Applies a change to the URL search params; filter changes reset the page. */
  onSearch: (change: Partial<ClaimSearch>) => void;
  /** Shown when the list is empty without any filter. */
  empty: { icon: ReactNode; title: string; body: string; action?: ReactNode };
  /** Shows only this kind, without the kind filter. */
  kind?: KindSlug;
};

/**
 * A claims list with search, filters, server-side sorting and paging, all kept
 * in the URL. Changing a filter keeps the old rows on screen until the new
 * ones arrive, so the list never flashes.
 */
export function ClaimsList({ scope, search: urlSearch, onSearch, empty, kind }: Props) {
  const t = useT();
  const isMobile = useIsMobile();
  const navigate = useNavigate();
  const search = kind ? { ...urlSearch, kind } : urlSearch;
  const query = useQuery(listClaims, listRequest(scope, search), { placeholderData: keepPreviousData });

  const claims = query.data?.claims ?? [];
  const total = query.data?.total ?? 0;
  const page = search.page ?? 1;
  const hasFilters = Boolean(search.q || (!kind && search.kind) || search.cc);
  const showOwner = !scope.mine;

  // Keyboard navigation: J/K move, Enter opens, / searches.
  const [activeIndex, setActiveIndex] = useState(-1);
  const searchRef = useRef<HTMLInputElement>(null);
  // biome-ignore lint/correctness/useExhaustiveDependencies: reset the cursor whenever the rows change
  useEffect(() => setActiveIndex(-1), [query.data]);
  const keysEnabled = !isMobile && claims.length > 0;
  const move = (delta: number) => {
    setActiveIndex((i) => Math.min(Math.max(i + delta, 0), claims.length - 1));
    // After React has marked the new row.
    requestAnimationFrame(() => document.querySelector("tr[data-active]")?.scrollIntoView({ block: "nearest" }));
  };
  useHotkey("J", () => move(1), { enabled: keysEnabled });
  useHotkey("K", () => move(-1), { enabled: keysEnabled });
  useHotkey(
    "Enter",
    () => {
      const claim = claims[activeIndex];
      if (claim) void navigate(claimLink(claim.kind, claim.number, scope.queue));
    },
    { enabled: keysEnabled && activeIndex >= 0 },
  );
  useHotkey("/", (event) => {
    event.preventDefault();
    searchRef.current?.focus();
  });

  const filterByCostCentre = useCallback((cc: string) => onSearch({ cc }), [onSearch]);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <SearchBox value={search.q ?? ""} onChange={(q) => onSearch({ q: q || undefined })} inputRef={searchRef} />
        {!kind && (
          <ToggleGroup
            variant="outline"
            value={[search.kind ?? "all"]}
            onValueChange={(value: string[]) => {
              const kind = value[0];
              if (kind) onSearch({ kind: kind === "all" ? undefined : (kind as KindSlug) });
            }}
          >
            {(["all", "expense", "invoice"] as const).map((kind) => (
              <ToggleGroupItem key={kind} value={kind} className="px-3">
                {t.claims.kindFilter[kind]}
              </ToggleGroupItem>
            ))}
          </ToggleGroup>
        )}
        {search.cc && (
          <Button variant="secondary" size="sm" onClick={() => onSearch({ cc: undefined })} className="gap-1.5">
            {t.claims.costCentreFilter(search.cc)}
            <X />
          </Button>
        )}
      </div>

      <Card className="relative gap-0 overflow-hidden p-0">
        {query.isFetching && !query.isPending && (
          <div className="absolute inset-x-0 top-0 z-20 h-0.5 overflow-hidden bg-primary/15">
            <div className="h-full w-1/3 animate-[loading-bar_1s_ease-in-out_infinite] bg-primary" />
          </div>
        )}

        {query.isPending ? (
          <ListSkeleton />
        ) : query.isError ? (
          <StateCard
            className="m-4 border-0"
            icon={<TriangleAlert />}
            title={t.claims.loadFailed}
            description={t.errors.generic}
            action={<Button onClick={() => void query.refetch()}>{t.errors.retry}</Button>}
          />
        ) : claims.length === 0 ? (
          hasFilters ? (
            <StateCard
              className="m-4 border-0"
              icon={<SearchIcon />}
              title={t.claims.noMatchesTitle}
              description={t.claims.noMatchesBody}
              action={
                <Button variant="outline" onClick={() => onSearch({ q: undefined, kind: undefined, cc: undefined })}>
                  {t.claims.clearFilters}
                </Button>
              }
            />
          ) : (
            <StateCard className="m-4 border-0" {...empty} description={empty.body} />
          )
        ) : isMobile ? (
          <ClaimCards claims={claims} showOwner={showOwner} queue={scope.queue} />
        ) : (
          <ClaimsTable
            claims={claims}
            showOwner={showOwner}
            sort={effectiveSort(scope, search)}
            onSortChange={(sort) => onSearch({ sort: sort.sort, desc: sort.desc || undefined })}
            onCostCentre={filterByCostCentre}
            activeIndex={activeIndex}
            queue={scope.queue}
          />
        )}
      </Card>

      {total > 0 && (
        <div className="flex items-center justify-between gap-4 text-muted-foreground text-sm">
          <span className="hidden items-center gap-1.5 md:flex">
            <Kbd>J</Kbd>
            <Kbd>K</Kbd>
            <Kbd>Enter</Kbd>
            <span className="sr-only">{t.claims.keyboardHint}</span>
          </span>
          <div className="ml-auto flex items-center gap-3">
            <span aria-live="polite">
              {t.claims.range((page - 1) * PAGE_SIZE + 1, Math.min(page * PAGE_SIZE, total), total)}
            </span>
            <Button
              variant="outline"
              size="icon-sm"
              aria-label={t.claims.previous}
              disabled={page <= 1}
              onClick={() => onSearch({ page: page - 1 > 1 ? page - 1 : undefined })}
            >
              <ChevronLeft />
            </Button>
            <Button
              variant="outline"
              size="icon-sm"
              aria-label={t.claims.next}
              disabled={page * PAGE_SIZE >= total}
              onClick={() => onSearch({ page: page + 1 })}
            >
              <ChevronRight />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Typing updates the box at once and the URL (and so the query) once the
 * user pauses. The box follows the URL when it changes elsewhere, e.g. when
 * filters are cleared.
 */
function SearchBox({
  value,
  onChange,
  inputRef,
}: {
  value: string;
  onChange: (q: string) => void;
  inputRef: React.Ref<HTMLInputElement>;
}) {
  const t = useT();
  const [text, setText] = useState(value);
  useEffect(() => setText(value), [value]);
  const commit = useDebouncedCallback(onChange, { wait: 250 });

  return (
    <div className="relative min-w-60 flex-1 md:max-w-sm">
      <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        ref={inputRef}
        type="search"
        value={text}
        placeholder={t.claims.search}
        aria-label={t.claims.search}
        className="pl-8"
        onChange={(event) => {
          setText(event.target.value);
          commit(event.target.value.trim());
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") event.currentTarget.blur();
        }}
      />
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="flex flex-col divide-y" aria-busy="true">
      {Array.from({ length: 6 }, (_, i) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: static placeholders
        <div key={i} className="flex h-14 items-center gap-4 px-4">
          <Skeleton className="h-4 w-10" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="hidden h-4 w-24 md:block" />
          <Skeleton className="h-4 w-20" />
        </div>
      ))}
    </div>
  );
}
