import { redirect, type RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async ({ fetch, cookies }) => {
	await fetch('http://localhost:8000/oidc/logout/', {
		method: 'POST',
		redirect: 'manual'
	});

	cookies.delete('sessionid', { path: '/' });
	cookies.delete('csrftoken', { path: '/' });

	throw redirect(303, '/login');
};
