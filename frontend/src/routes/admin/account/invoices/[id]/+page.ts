import type { PageLoad } from './$types';
import { loadAccounting } from '../../load';

export const load: PageLoad = ({ fetch, params }) =>
	loadAccounting(fetch, (api) => api.invoices.get(parseInt(params.id)));
