import type { ApiClient } from '#lib/api/client.ts';
import type { FortnoxAccount, FortnoxCostCentre, FortnoxStatus } from '#lib/api/types.ts';

export class FortnoxAPI {
	constructor(private apiClient: ApiClient) {}

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
