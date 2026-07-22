import { ApiClient } from '$lib/api';
import type {
	BudgetLine,
	CostCentre,
	PaginatedResponse,
	SecondaryCostCentre
} from '$lib/api/types';
import type { ListResponse } from '$lib/api/client';

function toPaginatedResponse<T>(res: ListResponse<T>): PaginatedResponse<T> {
	return {
		data: res.data,
		pagination: {
			page: res.pagination.page,
			perPage: res.pagination.per_page,
			totalPages: res.pagination.total_pages,
			total: res.pagination.total
		}
	};
}

export class BudgetAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	async listCostCentres(
		page: number,
		perPage: number,
		filter?: { active: boolean }
	): Promise<PaginatedResponse<CostCentre>> {
		const res = await this.apiClient.get<ListResponse<CostCentre>>('/cost-centres/', {
			page,
			per_page: perPage,
			...filter
		});

		return toPaginatedResponse(res);
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

		return toPaginatedResponse(res);
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

		return toPaginatedResponse(res);
	}
}
