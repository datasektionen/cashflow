import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { listParams, orEmptyPage } from '#lib/listParams.ts';
import type { ClaimOrdering } from '#lib/api/types.ts';
import { claimFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url, parent }) => {
	const api = new API(API_URL, fetch);

	const user = (await parent()).user!;

	const { page, perPage, sorting } = listParams<ClaimOrdering>(url, 15, ['-created_date']);

	const filter = claimFilterFromUrl(url);

	const claims = orEmptyPage(
		api.claims.list(page, perPage, { ...filter, user: user.username }, sorting),
		page,
		perPage
	);

	return { claims, user, title: `${user.first_name} ${user.last_name}`, ownHeader: true };
};
