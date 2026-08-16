import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';
import type { ClaimFilter, ClaimSorting } from '$lib/api/types';
import { claimFilterFromUrl } from '$lib/api/claimFilter';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);
	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	const sorting = (url.searchParams.get('sorting') as ClaimSorting | null) ?? undefined;

	const filter: ClaimFilter = {
		...claimFilterFromUrl(url),
		attestable: true,
		sorting
	};

	const claims = await api.claims.list(page, perPage, filter);

	return {
		title_key: 'admin_attestable.title',
		claims
	};
};
