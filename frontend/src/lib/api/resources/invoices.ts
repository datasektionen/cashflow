import { ApiClient } from '$lib/api';
import type { ClaimFilter, Invoice, InvoiceCreate, PaginatedResponse } from '$lib/api/types';

export class InvoicesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async get(id: number): Promise<Invoice> {
		return await this.apiClient.get<Invoice>(`invoices/${id}`);
	}

	async list(
		page: number,
		perPage: number,
		filter?: ClaimFilter
	): Promise<PaginatedResponse<Invoice>> {
		type RawResponse = {
			data: Invoice[];
			pagination: {
				total: number;
				page: number;
				per_page: number;
				total_pages: number;
			};
		};

		const res = await this.apiClient.get<RawResponse>('invoices/', {
			page,
			per_page: perPage,
			...filter
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

	comment(id: number, content: string) {
		return this.apiClient.post<Comment>(`invoices/${id}/comments/`, { content });
	}

	confirm(id: number) {
		return this.apiClient.post<void>(`invoices/${id}/confirm/`, {});
	}

	unconfirm(id: number) {
		return this.apiClient.post<void>(`invoices/${id}/unconfirm/`, {});
	}

	attestPart(partId: number) {
		return this.apiClient.post<void>(`invoice-parts/${partId}/attest/`, {});
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
