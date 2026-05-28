import type { PageLoad } from './$types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	const page = url.searchParams.get('page');
	const perPage = url.searchParams.get('per_page');

	return {
		title_key: 'admin_expenses.title',
		expenses: await api.expenses.list(page ? parseInt(page) : 1, perPage ? parseInt(perPage) : 10)
	};
};
