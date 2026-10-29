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
