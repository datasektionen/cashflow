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
		try {
			response = await this.fetch(`${this.apiUrl}${path.replace(/^\/+/, '')}`, {
				credentials: 'include',
				...options,
				// FormData and JSON data requires different headers
				// If we pass a Content-Type header with FormData, we will get errors that can be hard
				// to diagnose
				headers: {
					...(isFormData ? {} : { 'Content-Type': 'application/json' }),
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
			const error = (await response.json()) as ErrorResponse;
			log.error(
				{ path, status: response.status, duration_ms: duration, error },
				'API request failed'
			);
			throw error;
		}

		log.debug({ path, status: response.status, duration_ms: duration }, 'API request succeeded');
		return response.json();
	}

	get<T>(
		path: string,
		params?: Record<string, string | number | boolean | undefined>,
		options: RequestInit = {}
	): Promise<T> {
		const qs = params
			? '?' +
				new URLSearchParams(
					Object.entries(params)
						.filter(([, v]) => v !== undefined)
						.map(([k, v]) => [k, String(v)])
				).toString()
			: '';
		return this.request<T>(`${path}${qs}`, {
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
}
