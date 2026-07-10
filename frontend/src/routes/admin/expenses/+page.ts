import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { alerts, error } from '$lib/stores/alerts';
import type { ClaimFilter, Expense, PaginatedResponse } from '$lib/api/types';
import { isErrorResponse } from '$lib/api/errors';
import { logger } from '$lib/logger';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;
	const costCentre = url.searchParams.get('cost_centre') || undefined;
	const secondaryCostCentre = url.searchParams.get('secondary_cost_centre') || undefined;
	const budgetLine = url.searchParams.get('budget_line') || undefined;

	// Search queries
	const query = url.searchParams.get('q') || undefined;

	let expenses: PaginatedResponse<Expense> = {
		data: [],
		pagination: { total: 0, page, perPage, totalPages: 0 }
	};
	try {
		const filter: ClaimFilter = {
			cost_centre: costCentre,
			secondary_cost_centre: secondaryCostCentre,
			budget_line: budgetLine
		};

		expenses = query
			? await api.expenses.search(page, perPage, filter, { description_fuzzy: query })
			: await api.expenses.list(page, perPage, {
					cost_centre: costCentre,
					secondary_cost_centre: secondaryCostCentre,
					budget_line: budgetLine
				});
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
