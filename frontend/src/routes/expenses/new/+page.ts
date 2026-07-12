import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	return {
		title_key: 'new_expense.title'
	};
};
