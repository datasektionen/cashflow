import { assert, beforeEach, test, vi } from 'vitest';
import { ApiClient } from '$lib/api/client';

// mock the fetch function, we are only interested in the headers that were sent
// to the "server"
const fetch = vi.fn<typeof globalThis.fetch>(async () => {
	return new Response('{}', { status: 200 });
});
const client = new ApiClient('http://hej/', fetch);

beforeEach(() => {
	fetch.mockReset();
});

test('ensure no Content-Type for formdata requests', async () => {
	const data = new FormData();
	await client.post('/api/v1/', data);
	const headers = fetch.mock.calls[0][1]?.headers as Record<string, string> | undefined;
	assert(
		!('Content-Type' in headers!),
		'Content-Type header must not be set for FormData requests'
	);
});

test('ensure Content-Type is application/json for json requests', async () => {
	const data = { foo: 'bar' };
	await client.post('/api/v1/', data);
	const headers = fetch.mock.calls[0][1]?.headers as Record<string, string> | undefined;
	assert('Content-Type' in headers!, 'Content-Type must be set for JSON requests');
	assert(
		headers['Content-Type'] === 'application/json',
		"Content-Type must be 'application/json' for JSON requests"
	);
});
