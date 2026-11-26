import type { ApiClient } from '#lib/api/client.ts';
import type { PaginatedResponse, VoucherSeries } from '#lib/api/types.ts';

export class VoucherSeriesAPI {
	constructor(private apiClient: ApiClient) {}

	list(
		page: number,
		perPage: number,
		includeFortnox = true
	): Promise<PaginatedResponse<VoucherSeries>> {
		return this.apiClient.list('/voucher-series/', {
			page,
			per_page: perPage,
			include_fortnox: includeFortnox ? undefined : false
		});
	}
}
