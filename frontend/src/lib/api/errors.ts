/*
RFC 7807 style error objects, like the ones returned by the Cashflow API
 */
export interface ErrorResponse {
	type: string;
	title: string;
	detail: string;
	status: number;
	code: string;
}

export type NotAuthenticatedError = ErrorResponse & { code: 'not_authenticated' };

export function isErrorResponse(e: unknown): e is ErrorResponse {
	return typeof e === 'object' && e !== null && 'code' in e && 'status' in e;
}
