import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { defer } from '#lib/api/util.ts';
import { listParams } from '#lib/listParams.ts';
import { claimFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const { page, perPage } = listParams(url);

	const filter = claimFilterFromUrl(url);

	const payments = defer(
		api.payments.list(page, perPage, {
			tag: filter.reimbursement !== undefined ? String(filter.reimbursement) : undefined
		})
	);

	return { payments, title_key: 'admin_payments.title' };
};
