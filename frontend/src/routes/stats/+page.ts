import type { PageLoad } from './$types';
import { API } from '$lib/api';
import { API_URL } from '$lib/config';

export const load: PageLoad = async () => {
	return {
		title_key: 'leaderboard.title'
	};
};
