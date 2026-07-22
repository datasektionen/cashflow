import { redirect } from '@sveltejs/kit';
import { hasAdminAccess } from '$lib/auth';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async ({ parent }) => {
	const data = await parent();
	if (!hasAdminAccess(data.user)) {
		throw redirect(303, '/');
	}
	return data;
};
