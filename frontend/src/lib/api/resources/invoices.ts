import { ApiClient } from '$lib/api';
import type { Invoice, InvoiceCreate, PaginatedResponse } from '$lib/api/types';

class InvoicesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async list(page: number, perPage: number): Promise<PaginatedResponse<Invoice>> {
		type RawResponse = {
			data: Invoice[];
			pagination: {
				total: number;
				page: number;
				per_page: number;
				total_pages: number;
			};
		};

		const res = await this.apiClient.get<RawResponse>('invoices/', { page, per_page: perPage });

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

	async create(data: InvoiceCreate): Promise<Invoice> {
		return await this.apiClient.post<Invoice>('/invoices/', data, 'multipart/form-data');
	}
}
