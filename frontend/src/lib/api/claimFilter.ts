import type { ClaimFilter, TristateFilter } from '$lib/api/types';

const TRISTATE_KEYS = ['attested', 'confirmed', 'paid', 'accounted', 'flagged'] as const;

function tristateParam(url: URL, key: string): TristateFilter | undefined {
	const value = url.searchParams.get(key);
	return value === 'true' || value === 'false' || value === 'none' ? value : undefined;
}

/** Reimbursement is a numeric id; non-numeric input (e.g. a stray letter) must
 *  yield undefined rather than NaN, which the strict backend IntegerField rejects. */
function reimbursementParam(url: URL): number | undefined {
	const value = url.searchParams.get('reimbursement');
	if (!value) return undefined;
	const parsed = Number(value);
	return Number.isNaN(parsed) ? undefined : parsed;
}

/** Reads the filters ClaimFilterBar writes to the URL (cost centre, budget line,
 *  the tristate checkboxes, description search) into a ClaimFilter. */
export function claimFilterFromUrl(url: URL): ClaimFilter {
	const filter: ClaimFilter = {
		cost_centre: url.searchParams.get('cost_centre') || undefined,
		secondary_cost_centre: url.searchParams.get('secondary_cost_centre') || undefined,
		budget_line: url.searchParams.get('budget_line') || undefined,
		voucher_series: url.searchParams.get('voucher_series') || undefined,
		voucher_number: url.searchParams.get('voucher_number') || undefined,
		reimbursement: reimbursementParam(url),
		q: url.searchParams.get('q') || undefined
	};
	for (const key of TRISTATE_KEYS) {
		filter[key] = tristateParam(url, key);
	}
	return filter;
}
