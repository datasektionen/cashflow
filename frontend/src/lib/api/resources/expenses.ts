import { ApiClient } from '$lib/api';
import type {
	AccountPayload,
	ClaimFilter,
	Comment,
	DescriptionSearch,
	Expense,
	ExpenseCreate,
	ExpensePart,
	ExpenseUpdate,
	PaginatedResponse,
	PartCreateUpdate
} from '$lib/api/types';
import type { ListResponse } from '$lib/api/client';
import { toDecimal } from 'dinero.js';
import {
	type APIExpense,
	type APIExpensePart,
	parseExpense,
	parseExpensePart
} from '$lib/api/parse';

export class ExpensesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async get(id: number): Promise<Expense> {
		const expense = await this.apiClient.get<APIExpense>(`/expenses/${id}`);

		return parseExpense(expense);
	}

	async list(
		page: number,
		perPage: number,
		filter?: ClaimFilter
	): Promise<PaginatedResponse<Expense>> {
		const res = await this.apiClient.get<ListResponse<APIExpense>>('expenses/', {
			page: page,
			per_page: perPage,
			...filter
		});

		return {
			data: res.data.map(parseExpense),
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
		const res = await this.apiClient.query<ListResponse<APIExpense>>(
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
			data: res.data.map(parseExpense),
			pagination: {
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				total: res.pagination.total,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async create(data: ExpenseCreate): Promise<Expense> {
		const body = new FormData();
		body.append('description', data.description);
		body.append('expense_date', data.expense_date);

		type PartData = Omit<PartCreateUpdate, 'amount'> & { amount: string };

		const parts: PartData[] = data.parts.map((part) => ({
			...part,
			amount: toDecimal(part.amount)
		}));

		body.append('parts', JSON.stringify(parts));
		for (const file of data.files) {
			body.append('files', file, file.name);
		}

		return parseExpense(await this.apiClient.post<APIExpense>('expenses/', body));
	}

	async update(id: number, data: ExpenseUpdate): Promise<Expense> {
		const body = new FormData();
		if (data.description !== undefined) body.append('description', data.description);
		if (data.expense_date !== undefined) body.append('expense_date', data.expense_date);

		type PartData = Omit<PartCreateUpdate, 'amount'> & { amount: string };
		if (data.parts !== undefined) {
			const parts: PartData[] = data.parts.map((part) => ({
				...part,
				amount: toDecimal(part.amount)
			}));
			body.append('parts', JSON.stringify(parts));
		}

		if (data.delete_files !== undefined)
			body.append('delete_files', JSON.stringify(data.delete_files));
		for (const file of data.files ?? []) {
			body.append('files', file, file.name);
		}

		return parseExpense(await this.apiClient.patch<APIExpense>(`/expenses/${id}/`, body));
	}

	delete(id: number) {
		return this.apiClient.delete<APIExpense>(`/expenses/${id}/`, {});
	}

	comment(id: number, content: string) {
		return this.apiClient.post<Comment>(`/expenses/${id}/comments/`, { content: content });
	}

	async attestPart(partId: number): Promise<ExpensePart> {
		return parseExpensePart(
			await this.apiClient.post<APIExpensePart>(`/expense-parts/${partId}/attest/`, {})
		);
	}

	async unattestPart(partId: number): Promise<ExpensePart> {
		return parseExpensePart(
			await this.apiClient.post<APIExpensePart>(`/expense-parts/${partId}/unattest/`, {})
		);
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

	async account(id: number, payload: AccountPayload): Promise<Expense> {
		return parseExpense(await this.apiClient.post<APIExpense>(`/expenses/${id}/account/`, payload));
	}
}
