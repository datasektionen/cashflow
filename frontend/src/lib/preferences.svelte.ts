import { getContext, setContext } from 'svelte';

export type Preferences = { sidebarSlim: boolean; receiptWidth: number };

const COOKIE = 'preferences';
const KEY = Symbol('preferences');
export const DEFAULT_PREFERENCES: Preferences = { sidebarSlim: false, receiptWidth: 40 };

/** Reads the preferences cookie, ignoring anything malformed. */
export function parsePreferences(raw: string | undefined): Preferences {
	try {
		return { ...DEFAULT_PREFERENCES, ...JSON.parse(raw ?? '{}') };
	} catch {
		return { ...DEFAULT_PREFERENCES };
	}
}

/** Layout preferences for this page. Saved in a cookie so the server renders them too. */
export function setPreferences(initial: Preferences) {
	const prefs = $state(initial);
	$effect(() => {
		document.cookie = `${COOKIE}=${encodeURIComponent(JSON.stringify(prefs))}; path=/; max-age=31536000; samesite=lax`;
	});
	return setContext(KEY, prefs);
}

export const getPreferences = () => getContext<Preferences>(KEY);
