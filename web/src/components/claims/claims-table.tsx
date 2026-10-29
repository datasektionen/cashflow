import { useQuery } from "@connectrpc/connect-query";
import { Link } from "@tanstack/react-router";
import {
  createColumnHelper,
  flexRender,
  rowSortingFeature,
  type SortingState,
  tableFeatures,
  useTable,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import { useMemo } from "react";
import type { ClaimSummary } from "#/gen/cashflow/claim/v1/claim_pb";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { claimLink, formatDate, type QueueSlug, type SortSlug } from "#/lib/claims";
import { type Messages, useLocale, useT } from "#/lib/i18n";
import { canLookUpUsers } from "#/lib/navigation";
import { cn } from "#/lib/utils";
import { Amount, CostCentreChip, KindIcon, StageBadge } from "./badges";

const features = tableFeatures({ rowSortingFeature });
const column = createColumnHelper<typeof features, ClaimSummary>();

type Props = {
  claims: ClaimSummary[];
  showOwner: boolean;
  sort: { sort: SortSlug; desc: boolean };
  onSortChange: (sort: { sort: SortSlug; desc: boolean }) => void;
  onCostCentre: (cc: string) => void;
  activeIndex: number;
  /** The queue the list shows, carried to claim pages for "next in queue". */
  queue?: QueueSlug;
  /** The voucher number instead of the status, for lists of accounted claims. */
  showVoucher?: boolean;
};

/**
 * The desktop claims table. Sorting happens on the server, so the table only
 * renders and reports clicks. Each row's description is a real link stretched
 * over the row, so middle-click and cmd-click open new tabs.
 */
export function ClaimsTable({
  claims,
  showOwner,
  sort,
  onSortChange,
  onCostCentre,
  activeIndex,
  queue,
  showVoucher = false,
}: Props) {
  const t = useT();
  const caps = useQuery(getMe, {}).data?.capabilities;
  const ownerLinks = Boolean(caps && canLookUpUsers(caps));
  const locale = useLocale();

  const columns = useMemo(
    () => buildColumns(t, locale, showOwner, onCostCentre, queue, showVoucher, ownerLinks),
    [t, locale, showOwner, onCostCentre, queue, showVoucher, ownerLinks],
  );
  const sorting: SortingState = [{ id: sort.sort, desc: sort.desc }];

  const table = useTable({
    features,
    columns,
    data: claims,
    getRowId: (claim) => `${claim.kind}-${claim.number}`,
    manualSorting: true,
    enableSortingRemoval: false,
    state: { sorting },
    onSortingChange: (updater) => {
      const next = (typeof updater === "function" ? updater(sorting) : updater)[0];
      if (next) onSortChange({ sort: next.id as SortSlug, desc: next.desc });
    },
  });

  return (
    <table className="w-full table-fixed text-sm">
      <thead>
        {table.getHeaderGroups().map((group) => (
          <tr key={group.id} className="border-b text-left text-muted-foreground">
            {group.headers.map((header) => {
              const canSort = header.column.getCanSort();
              const direction = header.column.getIsSorted();
              const meta = header.column.columnDef.meta as ColumnMeta | undefined;
              return (
                <th
                  key={header.id}
                  scope="col"
                  aria-sort={direction ? (direction === "desc" ? "descending" : "ascending") : undefined}
                  className={cn("h-9 px-3 font-medium text-xs", meta?.className)}
                >
                  {canSort ? (
                    <button
                      type="button"
                      onClick={header.column.getToggleSortingHandler()}
                      title={t.claims.sortBy(String(header.column.columnDef.header))}
                      className={cn(
                        "-mx-1.5 inline-flex items-center gap-1 rounded px-1.5 py-1 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring",
                        meta?.align === "right" && "flex-row-reverse",
                        direction && "text-foreground",
                      )}
                    >
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {direction === "asc" ? (
                        <ArrowUp className="size-3.5" />
                      ) : direction === "desc" ? (
                        <ArrowDown className="size-3.5" />
                      ) : (
                        <ChevronsUpDown className="size-3.5 opacity-40" />
                      )}
                    </button>
                  ) : (
                    flexRender(header.column.columnDef.header, header.getContext())
                  )}
                </th>
              );
            })}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map((row, index) => (
          <tr
            key={row.id}
            data-active={index === activeIndex || undefined}
            className="group relative border-b transition-colors last:border-0 hover:bg-muted/60 data-active:bg-accent"
          >
            {row.getAllCells().map((cell) => {
              const meta = cell.column.columnDef.meta as ColumnMeta | undefined;
              return (
                <td key={cell.id} className={cn("h-10 px-3 py-1.5 align-middle", meta?.className)}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

type ColumnMeta = { className?: string; align?: "right" };

function buildColumns(
  t: Messages,
  locale: ReturnType<typeof useLocale>,
  showOwner: boolean,
  onCostCentre: (cc: string) => void,
  queue: QueueSlug | undefined,
  showVoucher: boolean,
  ownerLinks: boolean,
) {
  const c = t.claims.columns;
  return column.columns([
    column.accessor("number", {
      id: "number",
      header: c.number,
      enableSorting: false,
      meta: { className: "w-16" } satisfies ColumnMeta,
      cell: ({ row }) => (
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <KindIcon kind={row.original.kind} />
          <span className="amount text-xs">{row.original.number.toString()}</span>
        </span>
      ),
    }),
    column.accessor("description", {
      id: "description",
      header: c.description,
      cell: ({ row }) => (
        <div className="min-w-0">
          <Link
            {...claimLink(row.original.kind, row.original.number, queue)}
            className="block truncate font-medium outline-none after:absolute after:inset-0 focus-visible:after:ring-2 focus-visible:after:ring-ring focus-visible:after:ring-inset"
          >
            {row.original.description}
          </Link>
          {showOwner && (
            <span className="block truncate text-muted-foreground text-xs lg:hidden">{row.original.owner?.name}</span>
          )}
        </div>
      ),
    }),
    ...(showOwner
      ? [
          column.accessor((claim) => claim.owner?.name ?? "", {
            id: "owner",
            header: c.owner,
            meta: { className: "hidden w-40 lg:table-cell" } satisfies ColumnMeta,
            cell: ({ getValue, row }) => {
              const owner = row.original.owner;
              return ownerLinks && owner ? (
                // Above the row link, so it opens the person rather than the claim.
                <Link
                  to="/users/$username"
                  params={{ username: owner.username }}
                  title={t.users.view(owner.name)}
                  className="relative z-10 block truncate underline-offset-2 hover:underline"
                >
                  {getValue()}
                </Link>
              ) : (
                <span className="block truncate">{getValue()}</span>
              );
            },
          }),
        ]
      : []),
    column.accessor("costCentres", {
      id: "costCentres",
      header: c.costCentres,
      enableSorting: false,
      meta: { className: "hidden w-48 xl:table-cell" } satisfies ColumnMeta,
      cell: ({ getValue }) => {
        // One chip keeps every row one line high; the rest are named on hover.
        const [first, ...rest] = getValue();
        if (!first) return null;
        return (
          // Above the row link, so a chip filters instead of opening the claim.
          <div className="relative z-10 flex min-w-0 items-center gap-1">
            <CostCentreChip
              name={first}
              className="min-w-0 truncate"
              title={t.claims.filterByCostCentre(first)}
              onClick={() => onCostCentre(first)}
            />
            {rest.length > 0 && (
              <span className="shrink-0 text-muted-foreground text-xs" title={rest.join(", ")}>
                +{rest.length}
              </span>
            )}
          </div>
        );
      },
    }),
    column.accessor("date", {
      id: "date",
      header: c.date,
      meta: { className: "hidden w-28 md:table-cell" } satisfies ColumnMeta,
      cell: ({ getValue }) => <span className="text-muted-foreground">{formatDate(getValue(), locale)}</span>,
    }),
    column.accessor("amountOre", {
      id: "amount",
      header: c.amount,
      meta: { className: "w-32 text-right", align: "right" } satisfies ColumnMeta,
      cell: ({ getValue }) => <Amount ore={getValue()} />,
    }),
    showVoucher
      ? column.accessor((claim) => claim.status?.verification ?? "", {
          id: "voucher",
          header: c.voucher,
          enableSorting: false,
          meta: { className: "w-28 pl-6" } satisfies ColumnMeta,
          cell: ({ getValue }) => <span className="amount font-medium">{getValue()}</span>,
        })
      : column.accessor("status", {
          id: "status",
          header: c.status,
          enableSorting: false,
          meta: { className: "w-36 pl-6" } satisfies ColumnMeta,
          cell: ({ getValue }) => <StageBadge status={getValue()} />,
        }),
  ]);
}
