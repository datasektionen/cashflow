/**
 * Base API client class, gets subclassed for specific resources.
 */
export class ApiClient {
	private apiUrl: string;
	private fetch: typeof globalThis.fetch;

	constructor(apiUrl: string, fetch: typeof globalThis.fetch) {
		this.apiUrl = apiUrl;
		this.fetch = fetch;
	}

	private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
		const isFormData = options.body instanceof FormData;
		const response = await this.fetch(`${this.apiUrl}${path}`, {
			...options,
			headers: {
				...(isFormData ? {} : { 'Content-Type': 'application/json' }),
				...options.headers
			}
		});
		if (!response.ok) {
			const error = await response.json().catch(() => ({}));
			console.log('API error response:', error);
			throw new Error(error.message ?? `Request failed with status ${response.status}`);
		}

		return response.json();
	}

	post<T>(path: string, body: unknown) {
		return this.request<T>(path, {
			method: 'POST',
			body: body instanceof FormData ? body : JSON.stringify(body)
		});
	}
}
