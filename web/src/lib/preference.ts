import { useSyncExternalStore } from "react";

export type Preference<T extends string> = {
  get: () => T;
  set: (value: T) => void;
  subscribe: (listener: () => void) => () => void;
  /** Tells subscribers to re-read, for changes from outside `set` (e.g. the OS theme). */
  notify: () => void;
  fallback: () => T;
};

/**
 * A user preference kept in localStorage and shared across components.
 * `onChange` applies side effects (a class on <html>, the document language)
 * whenever the value is set, and once at startup.
 */
export function createPreference<T extends string>(options: {
  key: string;
  values: readonly T[];
  fallback: () => T;
  onChange?: (value: T) => void;
}): Preference<T> {
  const listeners = new Set<() => void>();

  const get = (): T => {
    if (typeof localStorage === "undefined") return options.fallback();
    const stored = localStorage.getItem(options.key);
    return options.values.find((v) => v === stored) ?? options.fallback();
  };

  const notify = () => {
    for (const listener of listeners) listener();
  };

  if (typeof window !== "undefined") options.onChange?.(get());

  return {
    get,
    set: (value) => {
      localStorage.setItem(options.key, value);
      options.onChange?.(value);
      notify();
    },
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    notify,
    fallback: options.fallback,
  };
}

/** The current value of a preference; re-renders when it changes. */
export function usePreference<T extends string>(preference: Preference<T>): T {
  return useSyncExternalStore(preference.subscribe, preference.get, preference.fallback);
}
