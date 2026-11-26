import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { listParams, orEmptyPage, titleOrNetworkError } from '#lib/listParams.ts';
import type { ClaimOrdering } from '#lib/api/types.ts';
import { claimFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url, params }) => {
	const api = new API(API_URL, fetch);

	const viewedUser = await api.users.retrieve(params.user);

	const { page, perPage, sorting } = listParams<ClaimOrdering>(url, 15, ['-created_date']);

	const claims = orEmptyPage(
		api.claims.list(page, perPage, { ...claimFilterFromUrl(url), user: params.user }, sorting),
		page,
		perPage,
		titleOrNetworkError
	);

	return {
		claims,
		viewedUser,
		title: `${viewedUser.first_name} ${viewedUser.last_name}`,
		ownHeader: true
	};
};
