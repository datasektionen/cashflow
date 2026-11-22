import type { ApiClient } from '#lib/api/client.ts';
import type { LeaderboardEntry, PaginatedResponse } from '#lib/api/types.ts';
import type { Dinero } from 'dinero.js';
import {
	type APILeaderboardEntry,
	type APIUserLeaderboardStats,
	type APIYearlyStatistics,
	parseLeaderboardEntry,
	parseYearlyStatistics
} from '#lib/api/parse.ts';

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
	constructor(private apiClient: ApiClient) {}

	leaderboard(
		page: number,
		perPage: number,
		startDate?: string,
		endDate?: string,
		orderBy?: '-expense_total' | 'expense_total' | '-expense_count' | 'expense_count'
	): Promise<PaginatedResponse<LeaderboardEntry>> {
		return this.apiClient.list(
			'/stats/leaderboard/',
			{
				page,
				per_page: perPage,
				start_date: startDate,
				end_date: endDate,
				ordering: orderBy ?? '-expense_total'
			},
			parseLeaderboardEntry<APILeaderboardEntry>
		);
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
		return parseLeaderboardEntry(
			await this.apiClient.get<APIUserLeaderboardStats>(
				`/stats/leaderboard/${encodeURIComponent(username)}/`,
				{ start_date: startDate, end_date: endDate }
			)
		);
	}
}
