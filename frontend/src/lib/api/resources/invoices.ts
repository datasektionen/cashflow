import type { ApiClient } from '#lib/api/client.ts';
import type {
	AccountPayload,
	Comment,
	Invoice,
	InvoiceCreate,
	InvoiceFilter,
	InvoiceOrdering,
	InvoiceUpdate,
	PaginatedResponse
} from '#lib/api/types.ts';
import { type APIInvoice, claimFormData, parseInvoice } from '#lib/api/parse.ts';

export class InvoicesAPI {
	constructor(private apiClient: ApiClient) {}

	async get(id: number): Promise<Invoice> {
		return parseInvoice(await this.apiClient.get<APIInvoice>(`invoices/${id}`));
	}

	list(
		page: number,
		perPage: number,
		filter?: InvoiceFilter,
		ordering?: InvoiceOrdering[]
	): Promise<PaginatedResponse<Invoice>> {
		return this.apiClient.list(
			'invoices/',
			{ page, per_page: perPage, ...filter, sorting: ordering?.join(',') },
			parseInvoice
		);
	}

	async create(data: InvoiceCreate): Promise<Invoice> {
		const fields = { ...data, verification: data.verification || undefined };
		return parseInvoice(await this.apiClient.post<APIInvoice>('invoices/', claimFormData(fields)));
	}

	async update(id: number, data: InvoiceUpdate): Promise<Invoice> {
		return parseInvoice(
			await this.apiClient.patch<APIInvoice>(`/invoices/${id}/`, claimFormData(data))
		);
	}

	delete(id: number) {
		return this.apiClient.delete<APIInvoice>(`/invoices/${id}/`, {});
	}

	comment(id: number, content: string) {
		return this.apiClient.post<Comment>(`invoices/${id}/comments/`, { content });
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
}
