import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { alerts, error } from '$lib/stores/alerts';
import type { ClaimSorting, Expense, PaginatedResponse } from '$lib/api/types';
import { isErrorResponse } from '$lib/api/errors';
import { logger } from '$lib/logger';
import { claimFilterFromUrl } from '$lib/api/claimFilter';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	// Sorting
	const sorting = (url.searchParams.get('sorting') as ClaimSorting | null) ?? undefined;

	const expenses = api.expenses
		.list(page, perPage, {
			sorting: sorting ? sorting : 'date',
			...claimFilterFromUrl(url),
			accountable: true
		})
		.catch((e): PaginatedResponse<Expense> => {
			if (!isErrorResponse(e)) throw e;
			logger.error(e);
			alerts.update((a) => [...a, error(e.detail)]);
			return { data: [], pagination: { total: 0, page, perPage, totalPages: 0 } };
		});

	return {
		title_key: 'admin_account.title',
		expenses
	};
};
