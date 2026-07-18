import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { isErrorResponse } from '$lib/api/errors';
import { alerts, error } from '$lib/stores/alerts';
import type { Claim, PaginatedResponse } from '$lib/api/types';
import { _, waitLocale } from 'svelte-i18n';
import { get } from 'svelte/store';
import { claimFilterFromUrl } from '$lib/api/claimFilter';

export const load: PageLoad = async ({ fetch, url, params }) => {
	const api = new API(API_URL, fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 10;

	let claims: PaginatedResponse<Claim> = {
		data: [],
		pagination: { total: 0, page, perPage, totalPages: 0 }
	};
	try {
		claims = await api.claims.list(page, perPage, {
			...claimFilterFromUrl(url),
			user: params.user,
			q: url.searchParams.get('q') || undefined
		});
	} catch (e) {
		if (isErrorResponse(e)) {
			let msg = e.status === 0 ? (await waitLocale(), get(_)('errors.network')) : e.title;
			alerts.update((a) => [...a, error(msg)]);
		} else {
			throw e;
		}
	}

	return { claims };
};
