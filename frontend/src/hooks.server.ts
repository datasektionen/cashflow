import type { Handle, HandleFetch } from '@sveltejs/kit/hooks';
import { logger } from '#lib/logger.ts';
import { API } from '#lib/api/index.ts';
import { API_URL } from '#lib/config.ts';

// Mirrors the paths nginx proxies to the backend (see nginx.conf).
const BACKEND_PATH = /^\/(api|admin|oidc|fortnox|static|media)(\/|$)/;

export const handle: Handle = async ({ event, resolve }) => {
	const { method, url } = event.request;
	logger.debug({ method, url }, 'incoming request');
	event.locals.user = event.cookies.get('sessionid')
		? await new API(API_URL, event.fetch).users.getCurrent().catch(() => null)
		: null;

	return resolve(event, {
		filterSerializedResponseHeaders: (name) => ['x-request-id', 'content-type'].includes(name)
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
