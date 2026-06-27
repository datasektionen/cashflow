import type { PageLoad } from './$types';
import type { PaginatedResponse, PendingPayment } from '$lib/api/types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	const pendingPayments: PaginatedResponse<PendingPayment> = await api.payments.listPending();

	return { title_key: 'admin_pay.title', pendingPayments: pendingPayments };
};
