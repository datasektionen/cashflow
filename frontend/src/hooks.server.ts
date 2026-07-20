import type { Handle, HandleFetch } from '@sveltejs/kit';
import { logger } from '$lib/logger';
import { API } from '$lib/api';
import { API_URL } from '$lib/config';

// Mirrors the paths nginx proxies to the backend (see nginx.conf).
const BACKEND_PATH = /^\/(api|admin|oidc|fortnox|static|media)(\/|$)/;

export const handle: Handle = async ({ event, resolve }) => {
	const { method, url } = event.request;
	logger.debug({ method, url }, 'incoming request');
	const api = new API(API_URL, event.fetch);
	event.locals.user = await api.users.getCurrent().catch(() => null);

	return resolve(event, {
		filterSerializedResponseHeaders: (name) =>
			name.toLowerCase() === 'x-request-id' || name.toLowerCase() === 'content-type'
	});
};

export const handleFetch: HandleFetch = async ({ event, request, fetch }) => {
	if (BACKEND_PATH.test(new URL(request.url).pathname)) {
		const headers = new Headers(request.headers);
		const sessionid = event.cookies.get('sessionid');
		const csrftoken = event.cookies.get('csrftoken');
		headers.set('cookie', `sessionid=${sessionid}; csrftoken=${csrftoken}`);
		if (csrftoken) headers.set('X-CSRFToken', csrftoken);
		request = new Request(request, { headers });
	}
	return fetch(request);
};
