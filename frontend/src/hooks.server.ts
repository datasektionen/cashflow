import type { HandleFetch } from '@sveltejs/kit';

export async function handle({ event, resolve }) {
	// Retrieve logged in (?) user from backend
	const res = await fetch('http://localhost:8000/users/me', {
		headers: {
			// The Django backend uses session authentication, so we need to send the session cookie with the request
			cookie: 'sessionid=' + event.cookies.get('sessionid')
		}
	}).catch((err) => {
		console.error('Error fetching user:', err);
		return { ok: false, json: JSON.parse(err) };
	});

	if (!res.ok) {
		event.locals.user = null;
	} else {
		const user = await res.json();
		event.locals.user = user?.username ? user : null;
	}
	return await resolve(event);
}

export const handleFetch: HandleFetch = async ({ event, request, fetch }) => {
	// Change all requests to the Django backend to include authentication
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
