import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { alerts, error } from '#lib/stores/alerts.ts';
import type { ExpenseOrdering } from '#lib/api/types.ts';
import { isErrorResponse } from '#lib/api/errors.ts';
import { logger } from '#lib/logger.ts';
import { claimFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	// Sorting
	const sortingParam = url.searchParams.get('sorting') as ExpenseOrdering | null;
	const sorting: ExpenseOrdering[] = sortingParam ? [sortingParam] : ['-created_date', '-id'];

	let expenses = null;
	try {
		const filter = claimFilterFromUrl(url);

		expenses = api.expenses.list(page, perPage, { ...filter }, sorting);
	} catch (e) {
		if (isErrorResponse(e)) {
			logger.error(e);
			alerts.update((a) => [...a, error(e.detail)]);
		} else {
			throw e;
		}
	}

	return {
		title_key: 'admin_expenses.title',
		expenses
	};
};
