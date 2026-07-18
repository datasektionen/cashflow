import { ApiClient } from '$lib/api';
import type { FortnoxAccount, FortnoxCostCentre, FortnoxStatus } from '$lib/api/types';

export class FortnoxAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	status(): Promise<FortnoxStatus> {
		return this.apiClient.get<FortnoxStatus>('/fortnox/status/');
	}

	disconnect(): Promise<FortnoxStatus> {
		return this.apiClient.post<FortnoxStatus>('/fortnox/disconnect/', {});
	}

	accounts(): Promise<FortnoxAccount[]> {
		return this.apiClient.get<FortnoxAccount[]>('/fortnox/accounts/');
	}

	costCentres(): Promise<FortnoxCostCentre[]> {
		return this.apiClient.get<FortnoxCostCentre[]>('/fortnox/cost-centres/');
	}
}
