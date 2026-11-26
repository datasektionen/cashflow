import { API_URL } from '#lib/config.ts';
import { API } from '#lib/api/index.ts';
import type { Expense, FortnoxAccount, FortnoxCostCentre, Invoice } from '#lib/api/types.ts';

/** Loads a claim and the Fortnox reference data for the accounting page. */
export async function loadAccounting(
	fetch: typeof globalThis.fetch,
	getClaim: (api: API) => Promise<Expense | Invoice>
) {
	const api = new API(API_URL, fetch);

	// Reference data is unavailable when the Fortnox integration is disabled
	// or disconnected; the page still works for manual voucher numbers.
	const [claim, accounts, costCentres] = await Promise.all([
		getClaim(api),
		api.fortnox.accounts().catch(() => [] as FortnoxAccount[]),
		api.fortnox.costCentres().catch(() => [] as FortnoxCostCentre[])
	]);

	return { title_key: 'admin_account.title', ownHeader: true, claim, accounts, costCentres };
}
