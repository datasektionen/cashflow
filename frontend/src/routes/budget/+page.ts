import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { API_URL } from '$lib/config';
import type { CostCentre, CostCentreFilter } from '$lib/api/types';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	let page = 1;
	let costCentres: CostCentre[] = [];

	const contains_blown: boolean | null = url.searchParams.get('contains_blown')
		? url.searchParams.get('contains_blown') === 'true'
		: null;

	const filter: CostCentreFilter = contains_blown
		? { active: true, contains_blown }
		: { active: true };

	do {
		const res = await api.budget.listCostCentres(page, 100, filter);

		costCentres.push(...res.data);

		if (page >= res.pagination.totalPages) {
			break;
		}
		page++;
	} while (true);

	return {
		costCentres,
		title_key: 'budget.title'
	};
};
