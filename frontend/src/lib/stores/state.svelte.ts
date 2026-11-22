import { MediaQuery } from 'svelte/reactivity';
import { api } from '#lib/api/index.ts';
import { logger } from '#lib/logger.ts';
import type { TableColumn } from '#lib/components/types.ts';

export const isExtraSmallLayout = new MediaQuery('max-width: 575.98px');
export const isSmallLayout = new MediaQuery('max-width: 767.98px'); // < md
export const isMediumLayout = new MediaQuery('max-width: 1023.98px'); // < lg
export const isLargeLayout = new MediaQuery('max-width: 1535.98px'); // < 2xl
let cachedProfilePicture: Promise<string | null> | undefined;

export function getProfilePicture(username: string): Promise<string | null> {
	if (cachedProfilePicture === undefined) {
		logger.debug({ username }, 'profile picture: cache miss, fetching');
		cachedProfilePicture = api.profilePictures
			.getMany([username])
			.then((pictures) => pictures[username] ?? null);
	} else {
		logger.debug({ username }, 'profile picture: cache hit');
	}
	return cachedProfilePicture;
}

export function clearProfilePicture(): void {
	cachedProfilePicture = undefined;
}

type Keep = string[] | null;
export type Layouts = { xs?: Keep; sm?: Keep; md?: Keep; lg?: Keep };

/**
 * Keeps the columns listed for the current breakpoint. A list also applies to smaller
 * breakpoints without their own; null or a larger screen shows all columns.
 */
export function byLayout<T>(cols: TableColumn<T>[], keep: Layouts): TableColumn<T>[] {
	const layouts = [
		[isExtraSmallLayout, keep.xs],
		[isSmallLayout, keep.sm],
		[isMediumLayout, keep.md],
		[isLargeLayout, keep.lg]
	] as const;
	for (const [query, ids] of layouts) {
		if (query.current && ids !== undefined)
			return ids ? cols.filter((c) => ids.includes(c.id)) : cols;
	}
	return cols;
}

// Where to return after accounting a claim, so the list keeps its filters
type Redirect = { id: string | null; url: URL | null };

const redirect: Redirect = $state({ id: null, url: null });

export function setRedirect(r: Redirect) {
	redirect.id = r.id;
	redirect.url = r.url;
}

export function getRedirect(): Redirect {
	return redirect;
}
