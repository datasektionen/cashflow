import type { PageLoad } from './$types';
import { API } from '$lib/api';
import type { ClaimFilter } from '$lib/api/types';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API('http://localhost:8000/api/', fetch);
	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	const filter: ClaimFilter = {
		type: 'expense',
		confirmable: true,
		cost_centre: url.searchParams.get('cost_centre') || undefined,
		secondary_cost_centre: url.searchParams.get('secondary_cost_centre') || undefined,
		budget_line: url.searchParams.get('budget_line') || undefined
	};

	const claims = await api.claims.list(page, perPage, filter);

	return {
		claims
	};
};
