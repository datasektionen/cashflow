import type { MessageInitShape } from "@bufbuild/protobuf";
import type { ListClaimsRequestSchema } from "#/gen/cashflow/claim/v1/claim_pb";
import {
  KINDS,
  type KindSlug,
  kindToProto,
  type QueueSlug,
  queueToProto,
  SORTS,
  type SortSlug,
  sortToProto,
} from "#/lib/claims";

/**
 * A claims list's state in the URL: shareable, survives reloads and the back
 * button. Only non-default values are kept, so URLs stay short.
 */
export type ClaimSearch = {
  q?: string;
  kind?: KindSlug;
  cc?: string;
  sort?: SortSlug;
  desc?: boolean;
  page?: number;
  /** A voucher series, e.g. "E", on lists of accounted claims. */
  series?: string;
};

const oneOf = <T extends string>(values: readonly T[], value: unknown): T | undefined =>
  values.find((v) => v === value);

/** For a route's validateSearch: keeps known keys with valid values, drops the rest. */
export function validateClaimSearch(raw: Record<string, unknown>): ClaimSearch {
  const text = (value: unknown) => (typeof value === "string" && value.trim() ? value : undefined);
  const page = typeof raw.page === "number" && Number.isInteger(raw.page) && raw.page > 1 ? raw.page : undefined;
  return {
    q: text(raw.q),
    kind: oneOf(KINDS, raw.kind),
    cc: text(raw.cc),
    sort: oneOf(SORTS, raw.sort),
    desc: raw.desc === true ? true : undefined,
    page,
    series: typeof raw.series === "string" && /^[A-Z]$/.test(raw.series) ? raw.series : undefined,
  };
}

/** Which claims a list shows: the caller's own, a work queue, or everything visible. */
export type ClaimScope = { mine?: boolean; queue?: QueueSlug; accounted?: boolean };

export const PAGE_SIZE = 25;

/**
 * The sort actually in effect. Without an explicit sort the server uses the
 * date: queues oldest first (worked through in order), other lists newest first.
 */
export function effectiveSort(scope: ClaimScope, search: ClaimSearch): { sort: SortSlug; desc: boolean } {
  return search.sort ? { sort: search.sort, desc: Boolean(search.desc) } : { sort: "date", desc: !scope.queue };
}

export function listRequest(scope: ClaimScope, search: ClaimSearch): MessageInitShape<typeof ListClaimsRequestSchema> {
  return {
    mine: Boolean(scope.mine),
    queue: scope.queue ? queueToProto[scope.queue] : undefined,
    kind: search.kind ? kindToProto[search.kind] : undefined,
    query: search.q,
    costCentre: search.cc,
    sort: search.sort ? sortToProto[search.sort] : undefined,
    descending: Boolean(search.desc),
    page: search.page ?? 1,
    pageSize: PAGE_SIZE,
    accounted: Boolean(scope.accounted),
    voucherSeries: search.series,
  };
}

/** Applies a change; any change other than paging starts again at page 1. */
export function applySearchChange(prev: ClaimSearch, change: Partial<ClaimSearch>): ClaimSearch {
  const next = { ...prev, ...change };
  if (!("page" in change)) next.page = undefined;
  return next;
}
