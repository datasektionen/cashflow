/**
 * Shared cache of GOrdian's cost centres, secondary cost centres and budget lines.
 * Each level is fetched once in full and grouped by parent id.
 */
import type { BudgetLine, CostCentre, SecondaryCostCentre } from '#lib/api/types.ts';
import { api } from '#lib/api/index.ts';
import { fetchAllPages } from '#lib/api/util.ts';

function groupBy<T>(items: T[], key: (item: T) => number | null): Map<number, T[]> {
	const groups = new Map<number, T[]>();
	for (const item of items) {
		const k = key(item);
		if (k == null) continue;
		groups.set(k, [...(groups.get(k) ?? []), item]);
	}
	return groups;
}

/** Caches the promise from `load`, dropping it on failure so the next call retries. */
function cached<T>(load: () => Promise<T>): () => Promise<T> {
	let promise: Promise<T> | undefined;
	return () =>
		(promise ??= load().catch((e) => {
			promise = undefined;
			throw e;
		}));
}

const loadCostCentres = cached(() =>
	fetchAllPages((page, perPage) => api.budget.listCostCentres(page, perPage))
);

const loadSecondary = cached(() =>
	fetchAllPages((page, perPage) => api.budget.listSecondaryCostCentres(page, perPage)).then((all) =>
		groupBy(all, (scc) => scc.cost_centre_id)
	)
);

const loadLines = cached(() =>
	fetchAllPages((page, perPage) => api.budget.listBudgetLines(page, perPage)).then((all) =>
		groupBy(all, (bl) => bl.secondary_cost_centre_id)
	)
);

export const budget = {
	costCentres: loadCostCentres,
	secondaryCostCentres: async (costCentre: CostCentre): Promise<SecondaryCostCentre[]> =>
		costCentre.id == null ? [] : ((await loadSecondary()).get(costCentre.id) ?? []),
	budgetLines: async (secondaryCostCentre: SecondaryCostCentre): Promise<BudgetLine[]> =>
		secondaryCostCentre.id == null ? [] : ((await loadLines()).get(secondaryCostCentre.id) ?? []),
	/** Starts fetching everything so later lookups resolve instantly. */
	preload() {
		for (const load of [loadCostCentres, loadSecondary, loadLines]) load().catch(() => {});
	}
};
