import type { Handle, HandleFetch } from '@sveltejs/kit';
import { logger } from '$lib/logger';
import { API } from '$lib/api';

export const handle: Handle = async ({ event, resolve }) => {
	const { method, url } = event.request;
	logger.debug({ method, url }, 'incoming request');
	const api = new API('http://localhost:8000/api/', event.fetch);
	event.locals.user = await api.users.getCurrent().catch(() => null);
	return resolve(event);
};

export const handleFetch: HandleFetch = async ({ event, request, fetch }) => {
	if (request.url.startsWith('http://localhost:8000')) {
		const headers = new Headers(request.headers);
		const sessionid = event.cookies.get('sessionid');
		const csrftoken = event.cookies.get('csrftoken');
		headers.set('cookie', `sessionid=${sessionid}; csrftoken=${csrftoken}`);
		if (csrftoken) headers.set('X-CSRFToken', csrftoken);
		request = new Request(request, { headers });
	}
	return fetch(request);
};
