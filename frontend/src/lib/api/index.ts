import { ExpensesAPI } from '#lib/api/resources/expenses.ts';
import { UsersAPI } from '#lib/api/resources/users.ts';
import { ApiClient } from '#lib/api/client.ts';
import { InvoicesAPI } from '#lib/api/resources/invoices.ts';
import { ClaimsAPI } from '#lib/api/resources/claims.ts';
import { ProfilePictureAPI } from '#lib/api/resources/profilePictures.ts';
import { PaymentsAPI } from '#lib/api/resources/payments.ts';
import { FortnoxAPI } from '#lib/api/resources/fortnox.ts';
import { BudgetAPI } from '#lib/api/resources/budget.ts';
import { VoucherSeriesAPI } from '#lib/api/resources/voucherSeries.ts';
import { StatsAPI } from '#lib/api/resources/stats.ts';
import { API_URL } from '#lib/config.ts';

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
	stats: StatsAPI;

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
		this.stats = new StatsAPI(client);
	}
}

export const api = new API(API_URL, fetch);
