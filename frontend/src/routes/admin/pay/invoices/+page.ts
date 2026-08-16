import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';
import type { ClaimSorting } from '$lib/api/types';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);
	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	const sorting = (url.searchParams.get('sorting') as ClaimSorting | null) ?? undefined;

	const invoices = await api.invoices.list(page, perPage, { payable: true, sorting });

	return { title_key: 'admin_pay.title', invoices };
};
