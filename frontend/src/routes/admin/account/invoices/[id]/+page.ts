import type { PageLoad } from './$types';
import { API } from '$lib/api';
import type { FortnoxAccount, FortnoxCostCentre } from '$lib/api/types';

export const load: PageLoad = async ({ fetch, params }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	// Reference data is unavailable when the Fortnox integration is disabled
	// or disconnected; the page still works for manual voucher numbers.
	const [invoice, accounts, costCentres] = await Promise.all([
		api.invoices.get(parseInt(params.id)),
		api.fortnox.accounts().catch(() => [] as FortnoxAccount[]),
		api.fortnox.costCentres().catch(() => [] as FortnoxCostCentre[])
	]);

	return {
		title_key: 'admin_account.title',
		invoice,
		accounts,
		costCentres
	};
};
