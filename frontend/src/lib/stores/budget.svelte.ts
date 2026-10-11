/**
 * This file contains shared state for budget-related data, including cost centres, secondary cost centres, and budget lines.
 */
import type { BudgetLine, CostCentre, SecondaryCostCentre } from '$lib/api/types';
import { SvelteMap } from 'svelte/reactivity';
import { logger } from '$lib/logger';
import { api } from '$lib/api';

class CostCentres {
	private costCentres: CostCentre[] = $state([]);

	private async refresh() {
		this.costCentres = await api.util.fetchAllPages((page, perPage) =>
			api.budget.listCostCentres(page, perPage)
		);
	}

	/**
	 * Lists all cost centres, fetching from the API if the cache is empty.
	 */
	async list(): Promise<CostCentre[]> {
		logger.debug('cost centres: listing');
		if (this.costCentres.length === 0) {
			logger.debug('cost centres: cache miss, fetching');
			await this.refresh();
		}
		return this.costCentres;
	}
}

class SecondaryCostCentres {
	private costCentres: CostCentres;
	private secondaryCostCentres: SvelteMap<CostCentre, SecondaryCostCentre[]> = $state(
		new SvelteMap<CostCentre, SecondaryCostCentre[]>()
	);

	constructor(costCentres: CostCentres) {
		this.costCentres = costCentres;
	}

	private async refresh() {
		const costCentres = await this.costCentres.list();
		await Promise.all(
			costCentres.map(async (cc) => {
				// Inactive cost centres have no id and thus no secondary cost centres
				if (cc.id == null) {
					this.secondaryCostCentres.set(cc, []);
					return;
				}
				const result = await api.util.fetchAllPages((page, perPage) =>
					api.budget.listSecondaryCostCentres(page, perPage, { cost_centre: cc.id! })
				);
				this.secondaryCostCentres.set(cc, result);
			})
		);
	}

	/**
	 * Lists all secondary cost centres, fetching from the API if the cache is empty.
	 *
	 * @returns A map of cost centres to their corresponding secondary cost centres.
	 */
	async list() {
		if (this.secondaryCostCentres.size === 0) {
			await this.refresh();
		}
		return this.secondaryCostCentres;
	}

	/**
	 * Retrieves the secondary cost centres for a specific cost centre, fetching from the API if the cache is empty.
	 * @param costCentre The cost centre for which to retrieve secondary cost centres.
	 * @returns An array of secondary cost centres for the specified cost centre, or undefined if not found.
	 */
	async get(costCentre: CostCentre): Promise<SecondaryCostCentre[] | undefined> {
		if (this.secondaryCostCentres.size === 0) {
			await this.refresh();
		}
		return this.secondaryCostCentres.get(costCentre);
	}
}

class BudgetLines {
	private budgetLines: SvelteMap<SecondaryCostCentre, BudgetLine[]> = $state(
		new SvelteMap<SecondaryCostCentre, BudgetLine[]>()
	);

	private async refresh(secondaryCostCentre: SecondaryCostCentre) {
		logger.debug(`budget lines: refreshing for secondary cost centre ${secondaryCostCentre.name}`);
		// Inactive secondary cost centres have no id and thus no budget lines
		if (secondaryCostCentre.id == null) {
			this.budgetLines.set(secondaryCostCentre, []);
			return;
		}
		const result: BudgetLine[] = await api.util.fetchAllPages((page, perPage) =>
			api.budget.listBudgetLines(page, perPage, {
				secondary_cost_centre: secondaryCostCentre.id!
			})
		);
		logger.debug(
			`budget lines: fetched ${result.length} lines for secondary cost centre ${secondaryCostCentre.name}`
		);
		this.budgetLines.set(secondaryCostCentre, result);
	}

	async get(secondaryCostCentre: SecondaryCostCentre): Promise<BudgetLine[] | undefined> {
		if (!this.budgetLines.has(secondaryCostCentre)) {
			await this.refresh(secondaryCostCentre);
		}
		return this.budgetLines.get(secondaryCostCentre);
	}
}

/**
 * "Wrapper" class for fetching budget information. Similar to how the API class is structured, it contains instances of resource-speciific classes (cost centres, secondary cost centres, and budget lines).
 */
class Budget {
	costCentres: CostCentres;
	secondaryCostCentres: SecondaryCostCentres;
	budgetLines: BudgetLines = new BudgetLines();

	constructor() {
		this.costCentres = new CostCentres();
		this.secondaryCostCentres = new SecondaryCostCentres(this.costCentres);
		this.budgetLines = new BudgetLines();
	}
}

export const budget = $state(new Budget());
