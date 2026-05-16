import type { Actions } from './$types';
import { API } from '$lib/api';

export const actions: Actions = {
	// This action handles the form submit when creating new expenses
	default: async (event) => {
		const api = new API('http://localhost:8000/api/', event.fetch);

		const data = await event.request.formData();
		api.expenses.create(data);
	}
};
