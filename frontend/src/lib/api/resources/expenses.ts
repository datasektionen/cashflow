import { ApiClient } from '$lib/api';

export class ExpensesAPI {
	private apiClient: ApiClient;

	constructor(apiClient: ApiClient) {
		this.apiClient = apiClient;
	}

	create(body: FormData) {
		this.apiClient.post('expenses/', body).then((r) => {
			console.log(r);
		});
	}
}
