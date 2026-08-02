import { browser } from '$app/environment';
import { init, register } from 'svelte-i18n';

const defaultLocale = 'sv';

export const LOCALE_STORAGE_KEY = 'locale';

/** Browser-side locale: the saved preference, else the browser's language. */
export function preferredLocale(): string {
	return localStorage.getItem(LOCALE_STORAGE_KEY) ?? window.navigator.language;
}

register('sv', () => import('./sv.json'));
register('en', () => import('./en.json'));

init({
	fallbackLocale: defaultLocale,
	initialLocale: browser ? preferredLocale() : defaultLocale
});
