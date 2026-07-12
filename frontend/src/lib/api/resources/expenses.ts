import { ApiClient } from '$lib/api';
import type {
	AccountPayload,
	ClaimFilter,
	Comment,
	DescriptionSearch,
	Expense,
	ExpenseCreate,
	ExpensePart,
	PaginatedResponse
} from '$lib/api/types';
import type { ListResponse } from '$lib/api/client';

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
		const res = await this.apiClient.get<ListResponse<Expense>>('expenses/', {
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

	async search(
		page: number,
		perPage: number,
		filter?: ClaimFilter,
		searchFields?: DescriptionSearch
	): Promise<PaginatedResponse<Expense>> {
		const res = await this.apiClient.query<ListResponse<Expense>>(
			'expenses/search/',
			{
				query: { ...filter, ...searchFields }
			},
			'application/json',
			{
				page: page,
				per_page: perPage
			}
		);

		return {
			data: res.data,
			pagination: {
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				total: res.pagination.total,
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

	account(id: number, payload: AccountPayload): Promise<Expense> {
		return this.apiClient.post<Expense>(`/expenses/${id}/account/`, payload);
	}
}
