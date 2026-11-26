import type { PageLoad } from './$types';
import { API } from '#lib/api/index.ts';
import { API_URL } from '#lib/config.ts';

export const load: PageLoad = async ({ fetch, url }) => {
	const thisYear = new Date().getFullYear();
	const requested = Math.trunc(Number(url.searchParams.get('year')));
	const year = requested ? Math.min(Math.max(requested, 2000), thisYear) : thisYear;
	// Awaited so the server renders the list; null shows the load error in the page
	const summary = await new API(API_URL, fetch).budget.summary(year).catch(() => null);
	return { year, summary, title_key: 'budget.title', ownHeader: true };
};
