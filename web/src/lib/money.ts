import { intlLocale, type Locale } from "#/lib/i18n";

/**
 * Formats an amount in öre as kronor with two decimals, without the currency,
 * e.g. 123450n → "1 234,50" in Swedish. Amounts are integers end to end; this
 * is the only place they become decimals.
 */
export function formatOre(ore: bigint, locale: Locale): string {
  const negative = ore < 0n;
  const abs = negative ? -ore : ore;
  const kronor = new Intl.NumberFormat(intlLocale[locale], { useGrouping: true }).format(abs / 100n);
  const decimal = new Intl.NumberFormat(intlLocale[locale]).formatToParts(1.5).find((p) => p.type === "decimal")?.value;
  const ore2 = (abs % 100n).toString().padStart(2, "0");
  return `${negative ? "−" : ""}${kronor}${decimal ?? ","}${ore2}`;
}

/**
 * Reads an amount the way people type it: "1 234,50", "1234.5", "12 kr".
 * Returns öre, or undefined if it isn't a non-negative amount with at most
 * two decimals. Parsed as text, so no floating point rounding.
 */
export function parseKronor(text: string): bigint | undefined {
  const cleaned = text
    .replace(/\s| | /g, "")
    .replace(/(kr|sek):?$/i, "")
    .replace(",", ".");
  const match = /^(\d+)(?:\.(\d{0,2}))?$/.exec(cleaned);
  if (!match) return undefined;
  const [, whole = "0", fraction = ""] = match;
  return BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0") || "0");
}

/** Öre as an editable amount, e.g. 123450n → "1234,50" (no grouping, so it parses back). */
export function oreToInput(ore: bigint, locale: Locale): string {
  const decimal = locale === "en" ? "." : ",";
  return `${ore / 100n}${decimal}${(ore % 100n).toString().padStart(2, "0")}`;
}
