import { ApiClient } from '$lib/api';
import type { User } from '$lib/api/types';

export class UsersAPI {
	private readonly apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async getCurrent(): Promise<User> {
		return this.apiClient.get<User>('/users/me');
	}
}
