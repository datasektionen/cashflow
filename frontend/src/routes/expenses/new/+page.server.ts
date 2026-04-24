import type { Actions } from './$types';

export const actions: Actions = {
	// This action handles the form submit when creating new expenses
	default: async (event) => {
		const contentType = event.request.headers.get('content-type') ?? '';
		const body = await event.request.arrayBuffer();

		const res = await event.fetch('http://localhost:8000/api/expenses/', {
			method: 'POST',
			headers: { 'Content-Type': contentType },
			body
		});
	}
};
