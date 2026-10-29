import { createPreference, usePreference } from "#/lib/preference";
import { en } from "./en";
import { type Messages, sv } from "./sv";

export const LOCALES = ["sv", "en"] as const;
export type Locale = (typeof LOCALES)[number];

const messages: Record<Locale, Messages> = { sv, en };

/** BCP 47 tags for Intl formatting. */
export const intlLocale: Record<Locale, string> = { sv: "sv-SE", en: "en-GB" };

const locale = createPreference<Locale>({
  key: "cashflow-locale",
  values: LOCALES,
  // Swedish unless the browser clearly prefers English.
  fallback: () => (typeof navigator !== "undefined" && navigator.language.startsWith("en") ? "en" : "sv"),
  onChange: (value) => {
    document.documentElement.lang = value;
  },
});

export const useLocale = () => usePreference(locale);
export const setLocale = locale.set;
export const getLocale = locale.get;

/** The current language's messages; re-renders when the language changes. */
export function useT(): Messages {
  return messages[useLocale()];
}

export type { Messages };
