import { ApiClient } from '$lib/api';
import type {
	ClaimFilter,
	Comment,
	Expense,
	ExpenseCreate,
	ExpensePart,
	PaginatedResponse
} from '$lib/api/types';

export class ExpensesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async get(id: number): Promise<Expense> {
		return await this.apiClient.get<Expense>(`/expenses/${id}`);
	}

	async list(
		page: number,
		perPage: number,
		filter?: ClaimFilter
	): Promise<PaginatedResponse<Expense>> {
		// The response format from DRF
		type RawResponse = {
			data: Expense[];
			pagination: {
				total: number;
				page: number;
				per_page: number;
				total_pages: number;
			};
		};

		const res = await this.apiClient.get<RawResponse>('expenses/', {
			page: page,
			per_page: perPage,
			...filter
		});

		return {
			data: res.data,
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}

	create(data: ExpenseCreate): Promise<Expense> {
		const body = new FormData();
		body.append('description', data.description);
		body.append('expense_date', data.expense_date);
		body.append('parts', JSON.stringify(data.parts));
		for (const file of data.files) {
			body.append('files', file, file.name);
		}

		return this.apiClient.post('expenses/', body);
	}

	comment(id: number, content: string) {
		return this.apiClient.post<Comment>(`/expenses/${id}/comments/`, { content: content });
	}

	attestPart(partId: number) {
		return this.apiClient.post<ExpensePart>(`/expense-parts/${partId}/attest/`, {});
	}

	confirm(id: number) {
		return this.apiClient.post<void>(`/expenses/${id}/confirm/`, {});
	}

	unconfirm(id: number) {
		return this.apiClient.post<void>(`/expenses/${id}/unconfirm/`, {});
	}

	flag(id: number) {
		return this.apiClient.post<void>(`/expenses/${id}/flag/`, {});
	}

	unflag(id: number) {
		return this.apiClient.post<void>(`/expenses/${id}/unflag/`, {});
	}
}
