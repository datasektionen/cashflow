import { ApiClient } from '$lib/api';
import type { Claim, ClaimFilter, ClaimOrdering, PaginatedResponse } from '$lib/api/types';
import { type APIClaim, parseClaim } from '$lib/api/parse';

export class ClaimsAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async list(
		page: number,
		perPage: number,
		filter?: ClaimFilter,
		ordering?: ClaimOrdering[]
	): Promise<PaginatedResponse<Claim>> {
		type RawResponse = {
			data: APIClaim[];
			pagination: {
				total: number;
				page: number;
				per_page: number;
				total_pages: number;
			};
		};

		const res = await this.apiClient.get<RawResponse>(`claims/`, {
			page,
			per_page: perPage,
			...filter,
			...(ordering ? { sorting: ordering.join(',') } : {})
		});

		return {
			data: res.data.map(parseClaim),
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}
}
