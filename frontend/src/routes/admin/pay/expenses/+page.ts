import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { fetchAllPages } from '#lib/api/util.ts';

export const load: PageLoad = async ({ fetch }) => {
	const api = new API(API_URL, fetch);
	const pendingPayments = await fetchAllPages((page, perPage) =>
		api.payments.listPending(page, perPage)
	);
	return { title_key: 'admin_pay.title', pendingPayments };
};
