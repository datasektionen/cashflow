import { ApiClient } from '$lib/api';
import type {
	BudgetLine,
	CostCentre,
	CostCentreFilter,
	PaginatedResponse,
	SecondaryCostCentre
} from '$lib/api/types';
import type { ListResponse } from '$lib/api/client';

export class BudgetAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async listCostCentres(
		page: number,
		perPage: number,
		filter?: CostCentreFilter
	): Promise<PaginatedResponse<CostCentre>> {
		const res = await this.apiClient.get<ListResponse<CostCentre>>('/cost-centres/', {
			page,
			per_page: perPage,
			...filter
		});

		return {
			data: res.data,
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async listSecondaryCostCentres(
		page: number,
		perPage: number,
		filter?: { active?: boolean; cost_centre?: number; costcentre_id?: number }
	): Promise<PaginatedResponse<SecondaryCostCentre>> {
		const res = await this.apiClient.get<ListResponse<SecondaryCostCentre>>(
			'/secondary-cost-centres/',
			{
				page,
				per_page: perPage,
				...filter
			}
		);

		return {
			data: res.data,
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async listBudgetLines(
		page: number,
		perPage: number,
		filter?: { active?: boolean; secondary_cost_centre?: number }
	): Promise<PaginatedResponse<BudgetLine>> {
		const res = await this.apiClient.get<ListResponse<BudgetLine>>('/budget-lines/', {
			page,
			per_page: perPage,
			...filter
		});

		return {
			data: res.data,
			pagination: {
				total: res.pagination.total,
				page: res.pagination.page,
				perPage: res.pagination.per_page,
				totalPages: res.pagination.total_pages
			}
		};
	}

	async getBudgetLine(id: number): Promise<BudgetLine> {
		return this.apiClient.get<BudgetLine>(`/budget-lines/${id}`);
	}

	async retrieveCostCentre(id: number): Promise<CostCentre> {
		return await this.apiClient.get<CostCentre>(`/cost-centres/${id}`);
	}
}
