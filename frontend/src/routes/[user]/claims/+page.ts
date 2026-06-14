import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { isErrorResponse } from '$lib/api/errors';
import { alerts, error } from '$lib/stores/alerts';
import type { Claim, PaginatedResponse } from '$lib/api/types';
import { _, waitLocale } from 'svelte-i18n';
import { get } from 'svelte/store';

export const load: PageLoad = async ({ fetch, url, params }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	const page = url.searchParams.get('page') ? parseInt(url.searchParams.get('page')!) : 1;
	const perPage = url.searchParams.get('per_page')
		? parseInt(url.searchParams.get('per_page')!)
		: 10;
	const costCentre = url.searchParams.get('cost_centre') || undefined;
	const secondaryCostCentre = url.searchParams.get('secondary_cost_centre') || undefined;
	const budgetLine = url.searchParams.get('budget_line') || undefined;

	let claims: PaginatedResponse<Claim> = {
		data: [],
		pagination: { total: 0, page, perPage, totalPages: 0 }
	};
	try {
		claims = await api.claims.list(page, perPage, {
			user: params.user,
			cost_centre: costCentre,
			secondary_cost_centre: secondaryCostCentre,
			budget_line: budgetLine
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
