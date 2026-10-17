import { ApiClient } from '$lib/api';
import type { Expense, PaginatedResponse, Payment, PendingPayment } from '$lib/api/types';
import {
	type APIPayment,
	type APIPendingPayment,
	parsePayment,
	parsePendingPayment
} from '$lib/api/parse';
import type { ListResponse } from '$lib/api/client';

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
		const res = await this.apiClient.get<ListResponse<APIPayment>>('/payments/', {
			page,
			per_page: perPage,
			...filter
		});
		return {
			data: res.data.map(parsePayment),
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async listPending(page?: number, perPage?: number): Promise<PaginatedResponse<PendingPayment>> {
		const res = await this.apiClient.get<ListResponse<APIPendingPayment>>('/payments/pending/', {
			page,
			per_page: perPage
		});
		return {
			data: res.data.map(parsePendingPayment),
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async create(expenses: number[] | Expense[]): Promise<Payment> {
		const expenseIds = expenses.map((e) => (typeof e === 'number' ? e : e.id));
		return parsePayment(
			await this.apiClient.post<APIPayment>('payments/', { expenses: expenseIds })
		);
	}
}
