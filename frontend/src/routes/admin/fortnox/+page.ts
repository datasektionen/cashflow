import { API_URL } from '#lib/config.ts';
import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import type { FortnoxStatus } from '#lib/api/types.ts';
import { failed } from '#lib/stores/alerts.ts';
import { isErrorResponse } from '#lib/api/errors.ts';

export const load: PageLoad = async ({ fetch }) => {
	const api = new API(API_URL, fetch);

	const status = await api.fortnox.status().catch((e): FortnoxStatus => {
		if (!isErrorResponse(e)) throw e;
		failed(e, e.detail);
		return { is_connected: false, authenticated_by: null, expires_at: null };
	});

	return {
		title_key: 'fortnox.title',
		status
	};
};
