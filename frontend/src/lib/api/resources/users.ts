import { ApiClient } from '$lib/api';
import type { ActionSummary, BankInfo, User } from '$lib/api/types';

export class UsersAPI {
	private readonly apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async getCurrent(): Promise<User> {
		return this.apiClient.get<User>('/users/me');
	}

	updateBankInfo(bankInfo: BankInfo): Promise<User> {
		return this.apiClient.patch<User>('/users/me/', { bank_info: bankInfo });
	}

	async actionSummary(): Promise<ActionSummary> {
		return this.apiClient.get<ActionSummary>('/actions');
	}
}
