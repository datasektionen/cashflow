import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { defer } from '#lib/api/util.ts';
import { listParams } from '#lib/listParams.ts';
import type { ClaimOrdering } from '#lib/api/types.ts';
import { claimFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);
	const { page, perPage, sorting } = listParams<ClaimOrdering>(url, 15, [
		'-type',
		'is_flagged',
		'date'
	]);

	return {
		title_key: 'admin_attestable.title',
		claims: defer(
			api.claims.list(page, perPage, { ...claimFilterFromUrl(url), attestable: true }, sorting)
		)
	};
};
