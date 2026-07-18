import { ApiClient } from '$lib/api';
import type { PaginatedResponse, VoucherSeries } from '$lib/api/types';
import type { ListResponse } from '$lib/api/client';

export class VoucherSeriesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async list(page: number, perPage: number): Promise<PaginatedResponse<VoucherSeries>> {
		const res = await this.apiClient.get<ListResponse<VoucherSeries>>('/voucher-series/', {
			page,
			perPage
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
