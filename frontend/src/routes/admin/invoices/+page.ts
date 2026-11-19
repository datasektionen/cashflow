import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { alerts, error } from '#lib/stores/alerts.ts';
import type { Invoice, InvoiceOrdering, PaginatedResponse } from '#lib/api/types.ts';
import { isErrorResponse } from '#lib/api/errors.ts';
import { logger } from '#lib/logger.ts';
import { invoiceFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 15;

	// Sorting
	const sortingParam = url.searchParams.get('sorting') as InvoiceOrdering | null;
	const sorting: InvoiceOrdering[] = sortingParam ? [sortingParam] : ['-created_date', '-id'];

	const filter = invoiceFilterFromUrl(url);

	const invoices = api.invoices
		.list(page, perPage, { ...filter }, sorting)
		.catch((e): PaginatedResponse<Invoice> => {
			if (!isErrorResponse(e)) throw e;
			logger.error(e);
			alerts.update((a) => [...a, error(e.detail)]);
			return { data: [], pagination: { total: 0, page, perPage, totalPages: 0 } };
		});

	return {
		title_key: 'admin_invoices.title',
		invoices
	};
};
