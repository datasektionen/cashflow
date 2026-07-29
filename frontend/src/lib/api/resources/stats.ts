import { ApiClient } from '$lib/api';
import type { LeaderboardEntry, PaginatedResponse } from '$lib/api/types';
import type { ListResponse } from '$lib/api/client';

export class StatsAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async leaderboard(
		page: number,
		perPage: number,
		startDate?: string,
		endDate?: string,
		orderBy?: '-expense_total' | 'expense_total' | '-expense_count' | 'expense_count'
	): Promise<PaginatedResponse<LeaderboardEntry>> {
		const params = {
			page,
			per_page: perPage,
			start_date: startDate,
			end_date: endDate,
			ordering: orderBy ? orderBy : '-expense_total'
		};
		const res = await this.apiClient.get<ListResponse<LeaderboardEntry>>(
			'/stats/leaderboard/',
			params
		);

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
