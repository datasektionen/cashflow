import { ClaimKind, Queue, SortField, Stage } from "#/gen/cashflow/claim/v1/claim_pb";
import { intlLocale, type Locale } from "#/lib/i18n";

/** Kinds as they appear in URLs: /expenses/12, ?kind=invoice. */
export const KINDS = ["expense", "invoice"] as const;
export type KindSlug = (typeof KINDS)[number];

export const kindToProto: Record<KindSlug, ClaimKind> = {
  expense: ClaimKind.EXPENSE,
  invoice: ClaimKind.INVOICE,
};

export function kindSlug(kind: ClaimKind): KindSlug {
  return kind === ClaimKind.INVOICE ? "invoice" : "expense";
}

/** The detail page of a claim. */
export function claimLink(kind: ClaimKind, number: bigint) {
  return kind === ClaimKind.INVOICE
    ? ({ to: "/invoices/$number", params: { number } } as const)
    : ({ to: "/expenses/$number", params: { number } } as const);
}

export const QUEUES = ["attest", "confirm", "account", "pay"] as const;
export type QueueSlug = (typeof QUEUES)[number];

export const queueToProto: Record<QueueSlug, Queue> = {
  attest: Queue.ATTEST,
  confirm: Queue.CONFIRM,
  account: Queue.ACCOUNT,
  pay: Queue.PAY,
};

export const SORTS = ["date", "amount", "description", "owner", "created"] as const;
export type SortSlug = (typeof SORTS)[number];

export const sortToProto: Record<SortSlug, SortField> = {
  date: SortField.DATE,
  amount: SortField.AMOUNT,
  description: SortField.DESCRIPTION,
  owner: SortField.OWNER,
  created: SortField.CREATED,
};

export const STAGES = ["submitted", "attested", "confirmed", "paid", "accounted"] as const;
export type StageSlug = (typeof STAGES)[number];

export const stageSlug: Record<Stage, StageSlug> = {
  [Stage.UNSPECIFIED]: "submitted",
  [Stage.SUBMITTED]: "submitted",
  [Stage.ATTESTED]: "attested",
  [Stage.CONFIRMED]: "confirmed",
  [Stage.PAID]: "paid",
  [Stage.ACCOUNTED]: "accounted",
};

/** The steps a claim goes through; invoices have no receipt to confirm. */
export function stepsFor(kind: ClaimKind): StageSlug[] {
  return kind === ClaimKind.INVOICE ? STAGES.filter((s) => s !== "confirmed") : [...STAGES];
}

/** Formats an ISO date (YYYY-MM-DD) for display; empty stays empty. */
export function formatDate(iso: string, locale: Locale, style: "short" | "long" = "short"): string {
  if (!iso) return "";
  const [y, m, d] = iso.split("-").map(Number);
  // Built from parts at noon UTC, so no time zone can shift the day.
  const date = new Date(Date.UTC(y ?? 1970, (m ?? 1) - 1, d ?? 1, 12));
  return new Intl.DateTimeFormat(intlLocale[locale], {
    dateStyle: style === "short" ? "medium" : "long",
    timeZone: "UTC",
  }).format(date);
}

/**
 * A stable hue for a cost centre, so the same name always gets the same
 * colour chip across pages. Hues near the brand green and the error red are
 * skipped, so chips never read as status.
 */
export function costCentreHue(name: string): number {
  let hash = 0;
  for (const char of name.toLowerCase()) hash = (hash * 31 + (char.codePointAt(0) ?? 0)) >>> 0;
  const usable = [45, 70, 95, 200, 225, 250, 275, 300, 325];
  return usable[hash % usable.length] ?? 250;
}
