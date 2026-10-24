import { ApiClient } from '$lib/api';
import type { LeaderboardEntry, PaginatedResponse } from '$lib/api/types';
import type { ListResponse } from '$lib/api/client';
import type { Dinero } from 'dinero.js';
import {
	type APILeaderboardEntry,
	type APIYearlyStatistics,
	parseLeaderboardEntry,
	parseYearlyStatistics
} from '$lib/api/parse';

export type MonthlyStatistics = {
	year: number;
	month: number;
	expense_count: number;
	invoice_count: number;
	expense_total: Dinero<number, 'SEK'>;
	invoice_total: Dinero<number, 'SEK'>;
};

export type YearlyStatistics = {
	year: number;
	months: MonthlyStatistics[];
};

export type UserLeaderboardStats = LeaderboardEntry & {
    amount_rank: number | null;
    count_rank: number | null;
};

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
		const res = await this.apiClient.get<ListResponse<APILeaderboardEntry>>(
			'/stats/leaderboard/',
			params
		);

		return {
			data: res.data.map(parseLeaderboardEntry),
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async yearly(year: number): Promise<YearlyStatistics> {
		return parseYearlyStatistics(
			await this.apiClient.get<APIYearlyStatistics>(`/stats/yearly/${year}/`)
		);
	}

	async userLeaderboard(
		username: string,
		startDate?: string,
		endDate?: string
	): Promise<UserLeaderboardStats> {
		const res = await this.apiClient.get<
			APILeaderboardEntry & {
				amount_rank: number;
				count_rank: number;
			}
		>(
			`/stats/leaderboard/${encodeURIComponent(username)}/`,
			{
				start_date: startDate,
				end_date: endDate
			}
		);

		return {
			...parseLeaderboardEntry(res),
			amount_rank: res.amount_rank,
			count_rank: res.count_rank
		};
	}
}
