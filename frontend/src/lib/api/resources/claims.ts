import { ApiClient } from '$lib/api';
import type { Claim, PaginatedResponse } from '$lib/api/types';

export class ClaimsAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async list(username: string, page: number, perPage: number): Promise<PaginatedResponse<Claim>> {
		type RawResponse = {
			data: Claim[];
			pagination: {
				total: number;
				page: number;
				per_page: number;
				total_pages: number;
			};
		};

		const res = await this.apiClient.get<RawResponse>(`${username}/claims/`, {
			page,
			per_page: perPage
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
}
