import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch, params }) => {
	const api = new API(API_URL, fetch);

	const expense = await api.expenses.get(parseInt(params.id));

	return { expense, title: expense.description };
};
