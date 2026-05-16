import { ExpensesAPI } from '$lib/api/resources/expenses';
import { ApiClient } from '$lib/api/client';

export { ApiClient } from './client';

export class API {
	expenses: ExpensesAPI;

	constructor(apiUrl: string, fetch: typeof globalThis.fetch) {
		const client = new ApiClient(apiUrl, fetch);
		this.expenses = new ExpensesAPI(client);
	}
}
