/** RFC 7807 style error, as returned by the Cashflow API. */
export interface ErrorResponse {
	type: string;
	title: string;
	detail: string;
	status: number;
	code: string;
}

export function isErrorResponse(e: unknown): e is ErrorResponse {
	return typeof e === 'object' && e !== null && 'detail' in e && 'status' in e;
}
