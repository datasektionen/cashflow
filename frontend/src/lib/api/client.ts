import { logger } from '#lib/logger.ts';
import type { ErrorResponse } from '#lib/api/errors.ts';
import type { PaginatedResponse } from '#lib/api/types.ts';

type Params = Record<string, string | number | boolean | undefined>;

export class ApiClient {
	constructor(
		private readonly apiUrl: string,
		private readonly fetch: typeof globalThis.fetch
	) {}

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
				// FormData must not get a Content-Type header
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
			const level = response.status === 401 || response.status === 403 ? 'warn' : 'error';
			log[level](
				{ path, status: response.status, duration_ms: duration, error },
				'API request failed'
			);
			throw error;
		}

		log.debug({ path, status: response.status, duration_ms: duration }, 'API request succeeded');
		if (response.status === 204) return undefined as T;
		return response.json();
	}

	private static queryString(params?: Params): string {
		return params
			? '?' +
					new URLSearchParams(
						Object.entries(params)
							.filter(([, v]) => v !== undefined)
							.map(([k, v]) => [k, String(v)])
					).toString()
			: '';
	}

	private send<T>(method: string, path: string, body: unknown) {
		return this.request<T>(path, {
			method,
			body: body instanceof FormData ? body : JSON.stringify(body)
		});
	}

	get<T>(path: string, params?: Params): Promise<T> {
		return this.request<T>(`${path}${ApiClient.queryString(params)}`, { method: 'GET' });
	}

	/** GETs a paginated endpoint and maps each item with `parse`. */
	async list<A, T = A>(
		path: string,
		params: Params,
		parse: (item: A) => T = (item) => item as unknown as T
	): Promise<PaginatedResponse<T>> {
		const { data, pagination: p } = await this.get<ListResponse<A>>(path, params);
		return {
			data: data.map((item) => parse(item)),
			pagination: { total: p.total, page: p.page, perPage: p.per_page, totalPages: p.total_pages }
		};
	}

	post<T>(path: string, body: unknown) {
		return this.send<T>('POST', path, body);
	}

	patch<T>(path: string, body: unknown) {
		return this.send<T>('PATCH', path, body);
	}

	delete<T>(path: string, body: unknown) {
		return this.send<T>('DELETE', path, body);
	}
}

type ListResponse<T> = {
	data: T[];
	pagination: {
		total: number;
		page: number;
		per_page: number;
		total_pages: number;
	};
};
