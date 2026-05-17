import { ApiClient } from '$lib/api';
import type { ExpenseCreate, Expense } from '$lib/api/types';

export class ExpensesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
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
}
