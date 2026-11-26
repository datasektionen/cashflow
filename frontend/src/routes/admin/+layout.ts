import { redirect } from '@sveltejs/kit';
import { hasAdminAccess } from '#lib/auth.ts';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ parent }) => {
	if (!hasAdminAccess((await parent()).user)) redirect(303, '/');
};
