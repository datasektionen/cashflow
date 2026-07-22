import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = ({ locals, url }) => {
	if (!locals.user && url.pathname !== '/login') {
		throw redirect(303, '/login');
	}
	if (locals.user && url.pathname === '/login') {
		throw redirect(303, '/');
	}
	return {
		user: locals.user
	};
};
