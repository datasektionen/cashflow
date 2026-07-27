import type { BudgetLine, CostCentre, SecondaryCostCentre } from '$lib/api/types';
import { SvelteMap } from 'svelte/reactivity';

export const cachedCostCentres: CostCentre[] = $state([]);

export const cachedSecondaryCostCentres: SvelteMap<CostCentre, SecondaryCostCentre[]> = $state(
	new SvelteMap<CostCentre, SecondaryCostCentre[]>()
);

export const cachedBudgetLines: SvelteMap<SecondaryCostCentre, BudgetLine[]> = $state(
	new SvelteMap<SecondaryCostCentre, BudgetLine[]>()
);
