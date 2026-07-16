import { ExpensesAPI } from '$lib/api/resources/expenses';
import { UsersAPI } from '$lib/api/resources/users';
import { ApiClient } from '$lib/api/client';
import { InvoicesAPI } from '$lib/api/resources/invoices';
import { ClaimsAPI } from '$lib/api/resources/claims';
import { ProfilePictureAPI } from '$lib/api/resources/profilePictures';
import { PaymentsAPI } from '$lib/api/resources/payments';
import { FortnoxAPI } from '$lib/api/resources/fortnox';
import { BudgetAPI } from '$lib/api/resources/budget';
import { VoucherSeriesAPI } from '$lib/api/resources/voucherSeries.js';
import { API_URL } from '$lib/config';

export { ApiClient } from './client';

export class API {
	expenses: ExpensesAPI;
	users: UsersAPI;
	invoices: InvoicesAPI;
	claims: ClaimsAPI;
	profilePictures: ProfilePictureAPI;
	payments: PaymentsAPI;
	fortnox: FortnoxAPI;
	budget: BudgetAPI;
	voucherSeries: VoucherSeriesAPI;

	constructor(apiUrl: string, fetch: typeof globalThis.fetch) {
		const client = new ApiClient(apiUrl.endsWith('/') ? apiUrl : apiUrl + '/', fetch);
		this.expenses = new ExpensesAPI(client);
		this.invoices = new InvoicesAPI(client);
		this.users = new UsersAPI(client);
		this.claims = new ClaimsAPI(client);
		this.profilePictures = new ProfilePictureAPI(client);
		this.payments = new PaymentsAPI(client);
		this.fortnox = new FortnoxAPI(client);
		this.budget = new BudgetAPI(client);
		this.voucherSeries = new VoucherSeriesAPI(client);
	}
}

export const api = new API(API_URL, fetch);
