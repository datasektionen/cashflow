import { ApiClient } from '$lib/api';
import type {
	AccountPayload,
	ClaimFilter,
	Comment,
	DescriptionSearch,
	Invoice,
	InvoiceCreate,
	InvoiceUpdate,
	PaginatedResponse,
	PartCreateUpdate
} from '$lib/api/types';
import { toDecimal } from 'dinero.js';
import { type APIInvoice, parseInvoice } from '$lib/api/parse';

// The response format from DRF
type RawResponse = {
	data: APIInvoice[];
	pagination: {
		total: number;
		page: number;
		per_page: number;
		total_pages: number;
	};
};

export class InvoicesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async get(id: number): Promise<Invoice> {
		return parseInvoice(await this.apiClient.get<APIInvoice>(`invoices/${id}`));
	}

	async list(
		page: number,
		perPage: number,
		filter?: ClaimFilter
	): Promise<PaginatedResponse<Invoice>> {
		const res = await this.apiClient.get<RawResponse>('invoices/', {
			page,
			per_page: perPage,
			...filter
		});

		return {
			data: res.data.map(parseInvoice),
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async search(
		page: number,
		perPage: number,
		filter?: ClaimFilter,
		searchFields?: DescriptionSearch
	): Promise<PaginatedResponse<Invoice>> {
		const res = await this.apiClient.query<RawResponse>(
			'invoices/search/',
			{
				query: { ...filter, ...searchFields }
			},
			'application/json',
			{
				page: page,
				per_page: perPage
			}
		);

		return {
			data: res.data.map(parseInvoice),
			pagination: {
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				total: res.pagination.total,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async update(id: number, data: InvoiceUpdate): Promise<Invoice> {
		const body = new FormData();
		if (data.description !== undefined) body.append('description', data.description);
		if (data.invoice_date !== undefined) body.append('invoice_date', data.invoice_date);
		if (data.due_date !== undefined) body.append('due_date', data.due_date);

		type PartData = Omit<PartCreateUpdate, 'amount'> & { amount: string };
		if (data.parts !== undefined) {
			const parts: PartData[] = data.parts.map((part) => ({
				...part,
				amount: toDecimal(part.amount)
			}));
			body.append('parts', JSON.stringify(parts));
		}

		if (data.delete_files !== undefined)
			body.append('delete_files', JSON.stringify(data.delete_files));
		for (const file of data.files ?? []) {
			body.append('files', file, file.name);
		}

		return parseInvoice(await this.apiClient.patch<APIInvoice>(`/invoices/${id}/`, body));
	}

	delete(id: number) {
		return this.apiClient.delete<APIInvoice>(`/invoices/${id}/`, {});
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

	unattestPart(partId: number) {
		return this.apiClient.post<void>(`invoice-parts/${partId}/unattest/`, {});
	}

	async pay(id: number): Promise<Invoice> {
		return parseInvoice(await this.apiClient.post<APIInvoice>(`invoices/${id}/pay/`, {}));
	}

	async account(id: number, payload: AccountPayload): Promise<Invoice> {
		return parseInvoice(await this.apiClient.post<APIInvoice>(`invoices/${id}/account/`, payload));
	}

	async create(data: InvoiceCreate): Promise<Invoice> {
		const body = new FormData();
		body.append('description', data.description);
		body.append('invoice_date', data.invoice_date);
		body.append('invoice_number', data.invoice_number);
		body.append('due_date', data.due_date);

		type PartData = Omit<PartCreateUpdate, 'amount'> & { amount: string };

		const parts: PartData[] = data.parts.map((part) => ({
			...part,
			amount: toDecimal(part.amount)
		}));

		body.append('parts', JSON.stringify(parts));
		if (data.accounted !== undefined) body.append('accounted', String(data.accounted));
		if (data.verification) body.append('verification', data.verification);
		for (const file of data.files) {
			body.append('files', file, file.name);
		}
		return parseInvoice(await this.apiClient.post<APIInvoice>('invoices/', body));
	}
}
