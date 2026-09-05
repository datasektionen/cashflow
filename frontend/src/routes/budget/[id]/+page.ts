import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { API_URL } from '$lib/config';

export const load: PageLoad = async ({ fetch, params }) => {
	const api = new API(API_URL, fetch);

	const id = parseInt(params.id);

	let page = 1;
	let costCentre;

	do {
		const res = await api.budget.listCostCentres(page, 100);
		costCentre = res.data.find((cc) => cc.id === id);

		if (costCentre || page >= res.pagination.totalPages) {
			break;
		}
		page++;
	} while (true);

	return {
		costCentre
	};
};
