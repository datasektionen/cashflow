import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import type { PaginatedResponse, PendingPayment } from '$lib/api/types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	const api = new API(API_URL, fetch);

	const perPage = 100;
	const first: PaginatedResponse<PendingPayment> = await api.payments.listPending(1, perPage);
	const rest = await Promise.all(
		Array.from({ length: Math.max(0, first.pagination.totalPages - 1) }, (_, i) =>
			api.payments.listPending(i + 2, perPage)
		)
	);

	const data = [...first.data, ...rest.flatMap((r) => r.data)];
	const pendingPayments: PaginatedResponse<PendingPayment> = {
		data,
		pagination: { ...first.pagination, page: 1, perPage: data.length, totalPages: 1 }
	};

	return { title_key: 'admin_pay.title', pendingPayments: pendingPayments };
};
