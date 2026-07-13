import type { PageLoad } from './$types';
import { API } from '$lib/api';

export const load: PageLoad = async ({ fetch, params }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	const expense = await api.expenses.get(parseInt(params.id));

	return { expense, title: expense.description };
};
