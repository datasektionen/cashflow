import type { ApiClient } from '#lib/api/client.ts';
import type { Claim, ClaimFilter, ClaimOrdering, PaginatedResponse } from '#lib/api/types.ts';
import { parseClaim } from '#lib/api/parse.ts';

export class ClaimsAPI {
	constructor(private apiClient: ApiClient) {}

	list(
		page: number,
		perPage: number,
		filter?: ClaimFilter,
		ordering?: ClaimOrdering[]
	): Promise<PaginatedResponse<Claim>> {
		return this.apiClient.list(
			'claims/',
			{ page, per_page: perPage, ...filter, sorting: ordering?.join(',') },
			parseClaim
		);
	}
}
