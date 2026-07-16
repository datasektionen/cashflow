import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import type { PaginatedResponse, PendingPayment } from '$lib/api/types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	const api = new API(API_URL, fetch);

	const pendingPayments: PaginatedResponse<PendingPayment> = await api.payments.listPending();

	return { title_key: 'admin_pay.title', pendingPayments: pendingPayments };
};
