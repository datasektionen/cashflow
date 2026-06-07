import { ApiClient } from '$lib/api';

export class ProfilePictureAPI {
	private client: ApiClient;

	constructor(client: ApiClient) {
		this.client = client;
	}

	async get(username: string): Promise<string | null> {
		const pictures = await this.getMany([username]);
		return pictures[username] ?? null;
	}

	getMany(usernames: string[]): Promise<Record<string, string | null>> {
		if (usernames.length === 0) return Promise.resolve({});
		return this.client.get<Record<string, string | null>>('/users/profile-pictures/', {
			usernames: usernames.join(',')
		});
	}
}
