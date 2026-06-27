import type { PageLoad } from './$types';
import type { Invoice, PaginatedResponse } from '$lib/api/types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	const invoices: PaginatedResponse<Invoice> = await api.invoices.list(1, 100, { payable: true });

	return { title_key: 'admin_pay.title', invoices };
};
