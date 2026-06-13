import { ExpensesAPI } from '$lib/api/resources/expenses';
import { UsersAPI } from '$lib/api/resources/users';
import { ApiClient } from '$lib/api/client';
import { InvoicesAPI } from '$lib/api/resources/invoices';
import { ClaimsAPI } from '$lib/api/resources/claims';
import { ProfilePictureAPI } from '$lib/api/resources/profilePictures';

export { ApiClient } from './client';

export class API {
	expenses: ExpensesAPI;
	users: UsersAPI;
	invoices: InvoicesAPI;
	claims: ClaimsAPI;
	profilePictures: ProfilePictureAPI;

	constructor(apiUrl: string, fetch: typeof globalThis.fetch) {
		const client = new ApiClient(apiUrl.endsWith('/') ? apiUrl : apiUrl + '/', fetch);
		this.expenses = new ExpensesAPI(client);
		this.invoices = new InvoicesAPI(client);
		this.users = new UsersAPI(client);
		this.claims = new ClaimsAPI(client);
		this.profilePictures = new ProfilePictureAPI(client);
	}
}

export const api = new API('http://localhost:8000/api/', fetch);
