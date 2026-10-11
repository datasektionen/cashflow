import { MediaQuery } from 'svelte/reactivity';
import { api } from '$lib/api';
import { logger } from '$lib/logger';

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
