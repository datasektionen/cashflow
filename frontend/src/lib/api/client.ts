import { logger } from '$lib/logger';
import type { ErrorResponse } from '$lib/api/errors';

/**
 * Base API client class, gets subclassed for specific resources.
 */
export class ApiClient {
	private readonly apiUrl: string;
	private readonly fetch: typeof globalThis.fetch;

	constructor(apiUrl: string, fetch: typeof globalThis.fetch) {
		this.apiUrl = apiUrl;
		this.fetch = fetch;
	}

	private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
		const isFormData = options.body instanceof FormData;
		const start = performance.now();
		let response: Response;

		const csrftoken =
			typeof document !== 'undefined' ? document.cookie.match(/csrftoken=([^;]+)/)?.[1] : undefined;

		try {
			response = await this.fetch(`${this.apiUrl}${path.replace(/^\/+/, '')}`, {
				credentials: 'include',
				...options,
				// FormData and JSON data requires different headers
				// If we pass a Content-Type header with FormData, we will get errors that can be hard
				// to diagnose
				headers: {
					...(isFormData ? {} : { 'Content-Type': 'application/json' }),
					...(csrftoken ? { 'X-CSRFToken': csrftoken } : {}),
					...options.headers
				}
			});
		} catch (e) {
			logger.error({ path, e }, 'API request failed');
			throw {
				type: 'about:blank',
				title: 'Network error',
				detail: 'API request failed',
				status: 0,
				code: 'network_error'
			} satisfies ErrorResponse;
		}

		const requestId = response.headers.get('X-Request-ID');
		const log = requestId ? logger.child({ request_id: requestId }) : logger;

		const duration = Math.round(performance.now() - start);

		if (!response.ok) {
			const contentType = response.headers.get('Content-Type') ?? '';
			const isJson =
				contentType.includes('application/json') ||
				contentType.includes('application/problem+json');
			const error: ErrorResponse = isJson
				? ((await response.json()) as ErrorResponse)
				: {
						type: 'about:blank',
						title: response.statusText || 'Error',
						detail: `Unexpected response from server (status ${response.status})`,
						status: response.status,
						code: 'unexpected_response'
					};
			log.error(
				{ path, status: response.status, duration_ms: duration, error },
				'API request failed'
			);
			throw error;
		}

		log.debug({ path, status: response.status, duration_ms: duration }, 'API request succeeded');
		if (response.status === 204) return undefined as T;
		return response.json();
	}

	private static queryString(
		params?: Record<string, string | number | boolean | undefined>
	): string {
		return params
			? '?' +
					new URLSearchParams(
						Object.entries(params)
							.filter(([, v]) => v !== undefined)
							.map(([k, v]) => [k, String(v)])
					).toString()
			: '';
	}

	get<T>(
		path: string,
		params?: Record<string, string | number | boolean | undefined>,
		options: RequestInit = {}
	): Promise<T> {
		return this.request<T>(`${path}${ApiClient.queryString(params)}`, {
			...options,
			method: 'GET'
		});
	}

	post<T>(path: string, body: unknown, contentType?: string) {
		return this.request<T>(path, {
			method: 'POST',
			body: body instanceof FormData ? body : JSON.stringify(body),
			...(contentType && { headers: { 'Content-Type': contentType } })
		});
	}

	query<T>(
		path: string,
		body: unknown,
		contentType?: string,
		params?: Record<string, string | number | boolean | undefined>
	) {
		return this.request<T>(`${path}${ApiClient.queryString(params)}`, {
			method: 'QUERY',
			body: body instanceof FormData ? body : JSON.stringify(body),
			...(contentType && { headers: { 'Content-Type': contentType } })
		});
	}

	patch<T>(path: string, body: unknown) {
		return this.request<T>(path, {
			method: 'PATCH',
			body: JSON.stringify(body)
		});
	}
}
export type ListResponse<T> = {
	data: T[];
	pagination: {
		total: number;
		page: number;
		per_page: number;
		total_pages: number;
	};
};
