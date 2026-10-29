import { useSyncExternalStore } from "react";

export type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "cashflow-theme";
const listeners = new Set<() => void>();
const media = () => window.matchMedia("(prefers-color-scheme: dark)");

function stored(): Theme {
  const value = localStorage.getItem(STORAGE_KEY);
  return value === "light" || value === "dark" ? value : "system";
}

/** Puts `.dark` on <html> to match the chosen theme (or the OS, for "system"). */
export function applyTheme() {
  const theme = stored();
  const dark = theme === "dark" || (theme === "system" && media().matches);
  document.documentElement.classList.toggle("dark", dark);
}

export function setTheme(theme: Theme) {
  if (theme === "system") localStorage.removeItem(STORAGE_KEY);
  else localStorage.setItem(STORAGE_KEY, theme);
  applyTheme();
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  const mq = media();
  const onChange = () => {
    applyTheme();
    listener();
  };
  mq.addEventListener("change", onChange);
  return () => {
    listeners.delete(listener);
    mq.removeEventListener("change", onChange);
  };
}

export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, stored, () => "system");
}
