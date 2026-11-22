import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { hasAdminAccess } from '#lib/auth.ts';
import { redirect } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch, params, parent }) => {
	const api = new API(API_URL, fetch);
	const { user } = await parent();

	if (params.user != user?.username && hasAdminAccess(user))
		redirect(303, `/admin/expenses/${params.id}/`);

	const expense = await api.expenses.get(parseInt(params.id));

	return { expense, title: expense.description, ownHeader: true };
};
