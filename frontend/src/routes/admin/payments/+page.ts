import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';

import { claimFilterFromUrl } from '$lib/api/claimFilter';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	const filter = claimFilterFromUrl(url);

	const payments = await api.payments.list(page, perPage, {
		tag: filter.reimbursement !== undefined ? String(filter.reimbursement) : undefined
	});

	return { payments, title_key: 'admin_payments.title' };
};
