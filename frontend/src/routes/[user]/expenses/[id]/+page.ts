import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { hasAdminAccess } from '$lib/auth';
import { redirect } from '@sveltejs/kit';

export const load: PageLoad = async ({ fetch, params, parent }) => {
	const api = new API(API_URL, fetch);
	const { user } = await parent();

	if (params.user != user?.username) {
		const url = `/admin/expenses/${params.id}/`;
		if (hasAdminAccess(user)) {
			redirect(303, url);
		}
	}

	const expense = await api.expenses.get(parseInt(params.id));

	return { expense, title: expense.description };
};
