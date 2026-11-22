import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';
import { parsePreferences } from '#lib/preferences.svelte.ts';

export const load: LayoutServerLoad = ({ locals, url, cookies }) => {
	if (!locals.user && url.pathname !== '/login') {
		throw redirect(303, '/login');
	}
	if (locals.user && url.pathname === '/login') {
		throw redirect(303, '/');
	}
	return {
		user: locals.user,
		preferences: parsePreferences(cookies.get('preferences'))
	};
};
