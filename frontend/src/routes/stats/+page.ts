import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { API_URL } from '#lib/config.ts';

export const load: PageLoad = async () => {
	return {
		title_key: 'stats.title'
	};
};
