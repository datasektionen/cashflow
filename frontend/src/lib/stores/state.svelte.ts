import type { BudgetLine, CostCentre, SecondaryCostCentre } from '$lib/api/types';
import { MediaQuery, SvelteMap } from 'svelte/reactivity';
import { api } from '$lib/api';
import { logger } from '$lib/logger';

export const isExtraSmallLayout = new MediaQuery('max-width: 575.98px');
export const isSmallLayout = new MediaQuery('max-width: 767.98px'); // < md
export const isMediumLayout = new MediaQuery('max-width: 1023.98px'); // < lg

export const cachedCostCentres: CostCentre[] = $state([]);

export const cachedSecondaryCostCentres: SvelteMap<CostCentre, SecondaryCostCentre[]> = $state(
	new SvelteMap<CostCentre, SecondaryCostCentre[]>()
);

export const cachedBudgetLines: SvelteMap<SecondaryCostCentre, BudgetLine[]> = $state(
	new SvelteMap<SecondaryCostCentre, BudgetLine[]>()
);

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
