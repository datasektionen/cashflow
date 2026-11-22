import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { listParams, orEmptyPage } from '#lib/listParams.ts';
import type { InvoiceOrdering } from '#lib/api/types.ts';
import { invoiceFilterFromUrl } from '#lib/api/claimFilter.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);

	const { page, perPage, sorting } = listParams<InvoiceOrdering>(url, 15, ['date']);

	return {
		title_key: 'admin_account.title',
		invoices: orEmptyPage(
			api.invoices.list(
				page,
				perPage,
				{ ...invoiceFilterFromUrl(url), accountable: true },
				sorting
			),
			page,
			perPage
		)
	};
};
