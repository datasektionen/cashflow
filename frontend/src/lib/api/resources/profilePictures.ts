import type { ApiClient } from '#lib/api/client.ts';

export class ProfilePictureAPI {
	constructor(private client: ApiClient) {}

	getMany(usernames: string[]): Promise<Record<string, string | null>> {
		if (usernames.length === 0) return Promise.resolve({});
		return this.client.get<Record<string, string | null>>('/users/profile-pictures/', {
			usernames: usernames.join(',')
		});
	}
}
