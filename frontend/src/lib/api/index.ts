import { ExpensesAPI } from '$lib/api/resources/expenses';
import { UsersAPI } from '$lib/api/resources/users';
import { ApiClient } from '$lib/api/client';

export { ApiClient } from './client';

export class API {
	expenses: ExpensesAPI;
	users: UsersAPI;

	constructor(apiUrl: string, fetch: typeof globalThis.fetch) {
		const client = new ApiClient(apiUrl, fetch);
		this.expenses = new ExpensesAPI(client);
		this.users = new UsersAPI(client);
	}
}

export const api = new API('http://localhost:8000/api/', fetch);
