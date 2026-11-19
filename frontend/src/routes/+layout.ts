import { browser } from '$app/env';
import { locale, waitLocale } from 'svelte-i18n';
import { preferredLocale } from '#lib/i18n/index.ts';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ data }) => {
	if (browser) {
		locale.set(preferredLocale());
	}
	await waitLocale();
	return data;
};
