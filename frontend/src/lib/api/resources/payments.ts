import { ApiClient } from '$lib/api';
import type { Expense, PaginatedResponse, Payment, PendingPayment } from '$lib/api/types';

export class PaymentsAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	listPending(): Promise<PaginatedResponse<PendingPayment>> {
		return this.apiClient.get<PaginatedResponse<PendingPayment>>('/payments/pending/');
	}

	create(expenses: number[] | Expense[]): Promise<Payment> {
		const expenseIds = expenses.map((e) => (typeof e === 'number' ? e : e.id));
		return this.apiClient.post<Payment>('payments/', { expenses: expenseIds });
	}
}
