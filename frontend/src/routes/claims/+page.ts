import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';
import type { ClaimOrdering } from '$lib/api/types';
import { _ } from 'svelte-i18n';
import { claimFilterFromUrl } from '$lib/api/claimFilter';

export const load: PageLoad = async ({ fetch, url, parent }) => {
	const api = new API(API_URL, fetch);

	const { user } = await parent();

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 10;

	const sortingParam = url.searchParams.get('sorting')?.split(',') as ClaimOrdering[] | null;
	const sorting: ClaimOrdering[] = sortingParam ?? ['-created_date'];

	const filter = claimFilterFromUrl(url);

	const claims = api.claims.list(page, perPage, { ...filter, user: user!.username }, sorting);

	return { claims };
};
