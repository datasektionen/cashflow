import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { alerts, error } from '$lib/stores/alerts';
import type { Invoice, PaginatedResponse } from '$lib/api/types';
import { isErrorResponse } from '$lib/api/errors';
import { logger } from '$lib/logger';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	let invoices: PaginatedResponse<Invoice> = {
		data: [],
		pagination: { total: 0, page, perPage, totalPages: 0 }
	};
	try {
		invoices = await api.invoices.list(page, perPage, { accountable: true });
	} catch (e) {
		if (isErrorResponse(e)) {
			logger.error(e);
			alerts.update((a) => [...a, error(e.detail)]);
		} else {
			throw e;
		}
	}

	return {
		title_key: 'admin_account.title',
		invoices
	};
};
