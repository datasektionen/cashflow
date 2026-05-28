import { logger } from '$lib/logger';

export class APIError extends Error {
	constructor(
		message: string,
		public status: number
	) {
		super(message);
		this.name = 'APIError';
	}
}

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
		let response: Response;
		try {
			response = await this.fetch(`${this.apiUrl}${path.replace(/^\/+/, '')}`, {
				credentials: 'include',
				...options,
				headers: {
					...(isFormData ? {} : { 'Content-Type': 'application/json' }),
					...options.headers
				}
			});
		} catch (e) {
			logger.error({ path, e }, 'API request failed');
			throw new APIError('API request failed', 0);
		}

		const requestId = response.headers.get('X-Request-ID');
		const log = requestId ? logger.child({ request_id: requestId }) : logger;

		if (!response.ok) {
			const error = await response.json().catch(() => ({}));
			const message =
				error.detail ?? error.title ?? `Request failed with status ${response.status}`;
			log.error({ path, status: response.status, error }, 'API request failed');
			throw new APIError(message, response.status);
		}

		log.debug({ path, status: response.status }, 'API request succeeded');
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

	post<T>(path: string, body: unknown) {
		return this.request<T>(path, {
			method: 'POST',
			body: body instanceof FormData ? body : JSON.stringify(body)
		});
	}
}
