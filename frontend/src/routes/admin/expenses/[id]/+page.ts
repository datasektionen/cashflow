import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';

export const load: PageLoad = ({ fetch, params }) => {
	const api = new API(API_URL, fetch);

	const expense = api.expenses.get(parseInt(params.id));

	return { expense, title: expense.then((e) => e.description).catch(() => ''), ownHeader: true };
};
