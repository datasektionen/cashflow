import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { listParams, orEmptyPage, titleOrNetworkError } from '#lib/listParams.ts';
import type { ClaimOrdering } from '#lib/api/types.ts';
import { claimFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const { page, perPage, sorting } = listParams<ClaimOrdering>(url, 15, ['-created_date']);

	return {
		claims: orEmptyPage(
			api.claims.list(page, perPage, { ...claimFilterFromUrl(url), accounted: 'true' }, sorting),
			page,
			perPage,
			titleOrNetworkError
		),
		title_key: 'admin_vouchers.title'
	};
};
