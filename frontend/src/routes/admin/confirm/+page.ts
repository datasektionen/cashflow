import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { defer } from '#lib/api/util.ts';
import { listParams } from '#lib/listParams.ts';
import type { ExpenseOrdering } from '#lib/api/types.ts';
import { claimFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);
	const { page, perPage, sorting } = listParams<ExpenseOrdering>(url, 15, ['is_flagged', 'date']);

	return {
		title_key: 'admin_confirmable.title',
		claims: defer(
			api.expenses.list(
				page,
				perPage,
				{ ...claimFilterFromUrl(url), type: 'expense', confirmable: true },
				sorting
			)
		)
	};
};
