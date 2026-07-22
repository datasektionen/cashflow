import { vi } from 'vitest';
import { init, register, waitLocale } from 'svelte-i18n';

export async function setupI18n(locale: 'sv' | 'en' = 'sv') {
	register('sv', () => import('$lib/i18n/sv.json'));
	register('en', () => import('$lib/i18n/en.json'));
	init({ fallbackLocale: 'sv', initialLocale: locale });
	await waitLocale(locale);
}

export function freezeTime(date: string, time = 'T12:00:00Z') {
	vi.useFakeTimers();
	vi.setSystemTime(new Date(`${date}${time}`));
}
