import { redirect, type RequestHandler } from '@sveltejs/kit';
import { BACKEND_URL } from '$lib/config';

export const POST: RequestHandler = async ({ fetch, cookies }) => {
	await fetch(`${BACKEND_URL}/oidc/logout/`, {
		method: 'POST',
		redirect: 'manual'
	});

	cookies.delete('sessionid', { path: '/' });
	cookies.delete('csrftoken', { path: '/' });

	throw redirect(303, '/login');
};
