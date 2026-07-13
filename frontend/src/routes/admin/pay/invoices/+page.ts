import type { PageLoad } from './$types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API('http://localhost:8000/api/', fetch);
	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	const invoices = await api.invoices.list(page, perPage, { payable: true });

	return { title_key: 'admin_pay.title', invoices };
};
