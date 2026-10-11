/**
 * Contains a class with utility methods for interacting with the API.
 */

import type { PaginatedResponse } from './types';

type FetchFunction<T> = (
	page: number,
	perPage: number,
	...args: any[]
) => Promise<PaginatedResponse<T>>;

export class ApiUtil {
	/**
	 * Fetches all pages of a paginated API endpoint and returns the joined items.
	 */
	async fetchAllPages<T>(fn: FetchFunction<T>, perPage: number = 100): Promise<T[]> {
		const firstPage = await fn(1, perPage);
		const rest = await Promise.all(
			Array.from({ length: firstPage.pagination.totalPages - 1 }, (_, i) => fn(i + 2, perPage))
		);
		return [firstPage, ...rest].flatMap((page) => page.data);
	}
}
