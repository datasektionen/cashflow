import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { defer } from '#lib/api/util.ts';
import { listParams } from '#lib/listParams.ts';
import type { InvoiceOrdering } from '#lib/api/types.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const api = new API(API_URL, fetch);
	const { page, perPage, sorting } = listParams<InvoiceOrdering>(url, 15, ['due_date', '-total']);

	return {
		title_key: 'admin_pay.title',
		invoices: defer(api.invoices.list(page, perPage, { payable: true }, sorting))
	};
};
