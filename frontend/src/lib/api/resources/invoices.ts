import { ApiClient } from '$lib/api';
import type { Invoice, InvoiceCreate, PaginatedResponse } from '$lib/api/types';

export class InvoicesAPI {
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
		const body = new FormData();
		body.append('description', data.description);
		body.append('invoice_date', data.invoice_date);
		body.append('due_date', data.due_date);
		body.append('parts', JSON.stringify(data.parts));
		if (data.accounted !== undefined) body.append('accounted', String(data.accounted));
		if (data.verification) body.append('verification', data.verification);
		for (const file of data.files) {
			body.append('files', file, file.name);
		}
		return await this.apiClient.post<Invoice>('invoices/', body);
	}
}
