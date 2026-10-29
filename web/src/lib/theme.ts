import { createPreference, usePreference } from "./preference";

export const THEMES = ["light", "dark", "system"] as const;
export type Theme = (typeof THEMES)[number];

const prefersDark = () => window.matchMedia("(prefers-color-scheme: dark)");

/** Puts `.dark` on <html>. Mirrored by THEME_SCRIPT in routes/__root.tsx, which runs before first paint. */
function apply(theme: Theme) {
  const dark = theme === "dark" || (theme === "system" && prefersDark().matches);
  document.documentElement.classList.toggle("dark", dark);
}

const theme = createPreference<Theme>({
  key: "cashflow-theme",
  values: THEMES,
  fallback: () => "system",
  onChange: apply,
});

// Follow the OS while the preference is "system".
if (typeof window !== "undefined") {
  prefersDark().addEventListener("change", () => {
    apply(theme.get());
    theme.notify();
  });
}

export const useTheme = () => usePreference(theme);
export const setTheme = theme.set;
