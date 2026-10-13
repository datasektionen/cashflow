import { ApiClient } from '$lib/api';
import type { Expense, PaginatedResponse, Payment, PendingPayment } from '$lib/api/types';
import {
	type APIPayment,
	type APIPendingPayment,
	parsePayment,
	parsePendingPayment
} from '$lib/api/parse';

export class PaymentsAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async list(
		page: number,
		perPage: number,
		filter?: { tag?: string }
	): Promise<PaginatedResponse<Payment>> {
		const res = await this.apiClient.get<PaginatedResponse<APIPayment>>('/payments/', {
			page,
			per_page: perPage,
			...filter
		});
		return { ...res, data: res.data.map(parsePayment) };
	}

	async listPending(page?: number, perPage?: number): Promise<PaginatedResponse<PendingPayment>> {
		const res = await this.apiClient.get<PaginatedResponse<APIPendingPayment>>(
			'/payments/pending/',
			{
				page,
				per_page: perPage
			}
		);
		return { ...res, data: res.data.map(parsePendingPayment) };
	}

	async create(expenses: number[] | Expense[]): Promise<Payment> {
		const expenseIds = expenses.map((e) => (typeof e === 'number' ? e : e.id));
		return parsePayment(
			await this.apiClient.post<APIPayment>('payments/', { expenses: expenseIds })
		);
	}
}
