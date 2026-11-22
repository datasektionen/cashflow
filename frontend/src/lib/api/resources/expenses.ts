import type { ApiClient } from '#lib/api/client.ts';
import type {
	AccountPayload,
	Comment,
	Expense,
	ExpenseCreate,
	ExpenseFilter,
	ExpenseOrdering,
	ExpenseUpdate,
	PaginatedResponse
} from '#lib/api/types.ts';
import { type APIExpense, claimFormData, parseExpense } from '#lib/api/parse.ts';

export class ExpensesAPI {
	constructor(private apiClient: ApiClient) {}

	async get(id: number): Promise<Expense> {
		return parseExpense(await this.apiClient.get<APIExpense>(`/expenses/${id}`));
	}

	list(
		page: number,
		perPage: number,
		filter?: ExpenseFilter,
		ordering?: ExpenseOrdering[]
	): Promise<PaginatedResponse<Expense>> {
		return this.apiClient.list(
			'expenses/',
			{ page, per_page: perPage, ...filter, sorting: ordering?.join(',') },
			parseExpense
		);
	}

	async create(data: ExpenseCreate): Promise<Expense> {
		return parseExpense(await this.apiClient.post<APIExpense>('expenses/', claimFormData(data)));
	}

	async update(id: number, data: ExpenseUpdate): Promise<Expense> {
		return parseExpense(
			await this.apiClient.patch<APIExpense>(`/expenses/${id}/`, claimFormData(data))
		);
	}

	delete(id: number) {
		return this.apiClient.delete<APIExpense>(`/expenses/${id}/`, {});
	}

	comment(id: number, content: string) {
		return this.apiClient.post<Comment>(`/expenses/${id}/comments/`, { content: content });
	}

	attestPart(partId: number) {
		return this.apiClient.post<void>(`/expense-parts/${partId}/attest/`, {});
	}

	unattestPart(partId: number) {
		return this.apiClient.post<void>(`/expense-parts/${partId}/unattest/`, {});
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
