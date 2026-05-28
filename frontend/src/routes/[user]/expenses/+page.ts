import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { APIError } from '$lib/api/client';
import { alerts, error } from '$lib/stores/alerts';
import type { Expense, PaginatedResponse } from '$lib/api/types';
import { _, waitLocale } from 'svelte-i18n';
import { get } from 'svelte/store';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 10;

	let expenses: PaginatedResponse<Expense> = {
		data: [],
		pagination: { total: 0, page, perPage, totalPages: 0 }
	};
	try {
		expenses = await api.expenses.list(page, perPage);
	} catch (e) {
		if (e instanceof APIError) {
			let msg = e.message;
			if (e.status === 0) {
				await waitLocale();
				msg = get(_)('errors.network');
			}
			alerts.update((a) => [...a, error(msg)]);
		} else {
			throw e;
		}
	}

	return {
		title_key: 'user_expenses',
		expenses
	};
};
