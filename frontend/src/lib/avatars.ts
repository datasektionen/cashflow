import { browser } from '$app/env';
import { api } from '#lib/api/index.ts';

let pending: { usernames: Set<string>; urls: Promise<Record<string, string | null>> } | undefined;

/** Looks up a profile picture, batching the lookups made in one render into one request. */
export function avatarUrl(username: string): Promise<string | null> {
	// Looked up in the browser only, where the session is
	if (!browser) return Promise.resolve(null);
	if (!pending) {
		const usernames = new Set<string>();
		const urls = Promise.resolve().then(() => {
			pending = undefined;
			return api.profilePictures.getMany([...usernames]).catch(() => ({}));
		});
		pending = { usernames, urls };
	}
	pending.usernames.add(username);
	return pending.urls.then((urls: Record<string, string | null>) => urls[username] ?? null);
}
