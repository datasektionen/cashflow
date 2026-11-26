import type { PaginatedResponse } from './types';

/**
 * Marks a promise a loader hands to its page as handled. Only the browser awaits it,
 * so a failed request during server rendering would otherwise crash the server.
 */
export function defer<T>(promise: Promise<T>): Promise<T> {
	promise.catch(() => {});
	return promise;
}

/** Fetches all pages of a paginated endpoint and returns the joined items. */
export async function fetchAllPages<T>(
	fn: (page: number, perPage: number) => Promise<PaginatedResponse<T>>,
	perPage = 100
): Promise<T[]> {
	const firstPage = await fn(1, perPage);
	const rest = await Promise.all(
		Array.from({ length: firstPage.pagination.totalPages - 1 }, (_, i) => fn(i + 2, perPage))
	);
	return [firstPage, ...rest].flatMap((page) => page.data);
}
