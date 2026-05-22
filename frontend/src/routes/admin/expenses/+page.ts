import type { PageLoad } from './$types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	return {
		title_key: 'admin_expenses.title',
		expenses: await api.expenses.list(1, 10)
	};
};
