import { MediaQuery } from 'svelte/reactivity';
import { api } from '#lib/api/index.ts';
import { logger } from '#lib/logger.ts';

export const isExtraSmallLayout = new MediaQuery('max-width: 575.98px');
export const isSmallLayout = new MediaQuery('max-width: 767.98px'); // < md
export const isMediumLayout = new MediaQuery('max-width: 1023.98px'); // < lg
let cachedProfilePicture: Promise<string | null> | undefined;

export function getProfilePicture(username: string): Promise<string | null> {
	if (cachedProfilePicture === undefined) {
		logger.debug({ username }, 'profile picture: cache miss, fetching');
		cachedProfilePicture = api.profilePictures.get(username);
	} else {
		logger.debug({ username }, 'profile picture: cache hit');
	}
	return cachedProfilePicture;
}

export function clearProfilePicture(): void {
	cachedProfilePicture = undefined;
}

type Redirect = {
	id: string | null;
	url: URL | null;
};

export let redirect: Redirect = $state({ id: null, url: null });

export function setRedirect(r: Redirect) {
	redirect.id = r.id;
	redirect.url = r.url;
}

export function getRedirect(): Redirect {
	return redirect;
}
