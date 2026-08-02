import { browser } from '$app/environment';
import { locale, waitLocale } from 'svelte-i18n';
import { preferredLocale } from '$lib/i18n';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ data }) => {
	if (browser) {
		locale.set(preferredLocale());
	}
	await waitLocale();
	return data;
};
