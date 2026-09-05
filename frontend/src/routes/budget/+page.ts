import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { API_URL } from '$lib/config';
import type { CostCentre } from '$lib/api/types';

export const load: PageLoad = async ({ fetch, params }) => {
	const api = new API(API_URL, fetch);

	let page = 1;
	let costCentres: CostCentre[] = [];

	do {
		const res = await api.budget.listCostCentres(page, 100, { active: true });

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
