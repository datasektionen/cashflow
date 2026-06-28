import type { PageLoad } from './$types';
import { API } from '$lib/api';
import type { FortnoxStatus } from '$lib/api/types';
import { alerts, error } from '$lib/stores/alerts';
import { isErrorResponse } from '$lib/api/errors';
import { logger } from '$lib/logger';

export const load: PageLoad = async ({ fetch }) => {
	const api = new API('http://localhost:8000/api/', fetch);

	let status: FortnoxStatus = {
		is_connected: false,
		authenticated_by: null,
		expires_at: null
	};
	try {
		status = await api.fortnox.status();
	} catch (e) {
		if (isErrorResponse(e)) {
			logger.error(e);
			alerts.update((a) => [...a, error(e.detail)]);
		} else {
			throw e;
		}
	}

	return {
		title_key: 'fortnox.title',
		status
	};
};
