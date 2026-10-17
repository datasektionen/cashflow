import { API_URL } from '$lib/config';
import type { PageLoad } from './$types';
import { API } from '$lib/api';

export const load: PageLoad = ({ fetch, params }) => {
	const api = new API(API_URL, fetch);

	const invoice = api.invoices.get(parseInt(params.id));

	return { invoice, title: invoice.then((i) => i.description) };
};
