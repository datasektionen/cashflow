import { type ErrorResponse, isErrorResponse } from '#lib/api/errors.ts';
import type { PaginatedResponse } from '#lib/api/types.ts';
import { defer } from '#lib/api/util.ts';
import { error } from '#lib/stores/alerts.ts';
import { logger } from '#lib/logger.ts';
import { _, waitLocale } from 'svelte-i18n';
import { get } from 'svelte/store';

export function listParams<S extends string = string>(url: URL, perPage = 15, sorting: S[] = []) {
	const params = url.searchParams;
	return {
		page: Number(params.get('page')) || 1,
		perPage: Number(params.get('per_page')) || perPage,
		sorting: (params.get('sorting')?.split(',') as S[] | undefined) ?? sorting
	};
}

/** Shows API errors as an alert and resolves to an empty page instead. */
export function orEmptyPage<T>(
	list: Promise<PaginatedResponse<T>>,
	page: number,
	perPage: number,
	message: (e: ErrorResponse) => string | Promise<string> = (e) => e.detail
): Promise<PaginatedResponse<T>> {
	return defer(
		list.catch(async (e) => {
			if (!isErrorResponse(e)) throw e;
			logger.error(e);
			error(await message(e));
			return { data: [], pagination: { total: 0, page, perPage, totalPages: 0 } };
		})
	);
}

export const titleOrNetworkError = async (e: ErrorResponse) => {
	if (e.status !== 0) return e.title;
	await waitLocale();
	return get(_)('errors.network');
};
