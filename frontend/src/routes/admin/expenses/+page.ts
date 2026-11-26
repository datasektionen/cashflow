import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { listParams, orEmptyPage } from '#lib/listParams.ts';
import type { ExpenseOrdering } from '#lib/api/types.ts';
import { claimFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const { page, perPage, sorting } = listParams<ExpenseOrdering>(url, 15, ['-created_date', '-id']);

	return {
		title_key: 'admin_expenses.title',
		expenses: orEmptyPage(
			api.expenses.list(page, perPage, claimFilterFromUrl(url), sorting),
			page,
			perPage
		)
	};
};
