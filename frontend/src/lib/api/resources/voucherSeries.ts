import { ApiClient } from '$lib/api';
import type { PaginatedResponse, VoucherSeries } from '$lib/api/types';
import type { ListResponse } from '$lib/api/client';

export class VoucherSeriesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async list(
		page: number,
		perPage: number,
		includeFortnox: boolean = true
	): Promise<PaginatedResponse<VoucherSeries>> {
		let params: { page: number; perPage: number; include_fortnox?: boolean } = {
			page,
			perPage
		};
		if (!includeFortnox) {
			params = { ...params, include_fortnox: false };
		}
		const res = await this.apiClient.get<ListResponse<VoucherSeries>>('/voucher-series/', params);

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
