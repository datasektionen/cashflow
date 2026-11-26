import type { ApiClient } from '#lib/api/client.ts';
import type { Expense, PaginatedResponse, Payment, PendingPayment } from '#lib/api/types.ts';
import { type APIPayment, parsePayment, parsePendingPayment } from '#lib/api/parse.ts';

export class PaymentsAPI {
	constructor(private apiClient: ApiClient) {}

	list(
		page: number,
		perPage: number,
		filter?: { tag?: string }
	): Promise<PaginatedResponse<Payment>> {
		return this.apiClient.list('/payments/', { page, per_page: perPage, ...filter }, parsePayment);
	}

	listPending(page: number, perPage: number): Promise<PaginatedResponse<PendingPayment>> {
		return this.apiClient.list(
			'/payments/pending/',
			{ page, per_page: perPage },
			parsePendingPayment
		);
	}

	async create(expenses: number[] | Expense[]): Promise<Payment> {
		const expenseIds = expenses.map((e) => (typeof e === 'number' ? e : e.id));
		return parsePayment(
			await this.apiClient.post<APIPayment>('payments/', { expenses: expenseIds })
		);
	}
}
