import { ApiClient } from '$lib/api';
import type { ActionSummary, User } from '$lib/api/types';

export class UsersAPI {
	private readonly apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async getCurrent(): Promise<User> {
		return this.apiClient.get<User>('/users/me');
	}

	async actionSummary(): Promise<ActionSummary> {
		return this.apiClient.get<ActionSummary>('/actions');
	}
}
