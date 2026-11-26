import type { ApiClient } from '#lib/api/client.ts';
import type { ActionOverview, ActionSummary, BankInfo, User } from '#lib/api/types.ts';

export class UsersAPI {
	constructor(private apiClient: ApiClient) {}

	getCurrent(): Promise<User> {
		return this.apiClient.get<User>('/users/me/');
	}

	retrieve(username: string): Promise<User> {
		return this.apiClient.get<User>(`/users/${username}`);
	}

	updateBankInfo(bankInfo: BankInfo): Promise<User> {
		return this.apiClient.patch<User>('/users/me/', { bank_info: bankInfo });
	}

	actionSummary(): Promise<ActionSummary> {
		return this.apiClient.get<ActionSummary>('/actions');
	}

	actionOverview(): Promise<ActionOverview> {
		return this.apiClient.get<ActionOverview>('/actions/overview');
	}
}
