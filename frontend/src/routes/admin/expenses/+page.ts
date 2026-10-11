import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { alerts, error } from '$lib/stores/alerts';
import type { ClaimSorting } from '$lib/api/types';
import { isErrorResponse } from '$lib/api/errors';
import { logger } from '$lib/logger';
import { claimFilterFromUrl } from '$lib/api/claimFilter';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	// Search queries
	const query = url.searchParams.get('q') || undefined;

	// Sorting
	const sorting = (url.searchParams.get('sorting') as ClaimSorting | null) ?? undefined;

	let expenses = null;
	try {
		const filter = claimFilterFromUrl(url);

		expenses = query
			? api.expenses.search(page, perPage, { ...filter, sorting }, { description_fuzzy: query })
			: api.expenses.list(page, perPage, { ...filter, sorting });
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
