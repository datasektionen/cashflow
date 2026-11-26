import type { ApiClient } from '#lib/api/client.ts';
import type {
	BudgetLine,
	CostCentre,
	CostCentreFilter,
	CostCentreSummary,
	PaginatedResponse,
	SecondaryCostCentre
} from '#lib/api/types.ts';

export class BudgetAPI {
	constructor(private apiClient: ApiClient) {}

	listCostCentres(
		page: number,
		perPage: number,
		filter?: CostCentreFilter
	): Promise<PaginatedResponse<CostCentre>> {
		return this.apiClient.list('/cost-centres/', { page, per_page: perPage, ...filter });
	}

	listSecondaryCostCentres(
		page: number,
		perPage: number,
		filter?: { active?: boolean; cost_centre?: number; costcentre_id?: number }
	): Promise<PaginatedResponse<SecondaryCostCentre>> {
		return this.apiClient.list('/secondary-cost-centres/', { page, per_page: perPage, ...filter });
	}

	listBudgetLines(
		page: number,
		perPage: number,
		filter?: { active?: boolean; secondary_cost_centre?: number }
	): Promise<PaginatedResponse<BudgetLine>> {
		return this.apiClient.list('/budget-lines/', { page, per_page: perPage, ...filter });
	}

	getBudgetLine(id: number): Promise<BudgetLine> {
		return this.apiClient.get<BudgetLine>(`/budget-lines/${id}`);
	}

	retrieveCostCentre(id: number, year?: number): Promise<CostCentre> {
		return this.apiClient.get<CostCentre>(`/cost-centres/${id}`, year ? { year } : undefined);
	}

	summary(year: number): Promise<CostCentreSummary[]> {
		return this.apiClient.get<CostCentreSummary[]>('/cost-centres/summary/', { year });
	}
}
