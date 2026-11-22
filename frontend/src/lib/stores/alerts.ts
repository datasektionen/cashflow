import { writable } from 'svelte/store';
import { browser } from '$app/env';
import { isErrorResponse } from '#lib/api/errors.ts';
import { logger } from '#lib/logger.ts';

export type Alert = {
	id: string;
	type: 'success' | 'warning' | 'error';
	message: string;
	duration: number;
};

export const alerts = writable<Alert[]>([]);

// Browser only: on the server this store is shared by every request, so a toast would reach everyone.
// Loads run again in the browser on hydration, so their errors still show.
const show = (type: Alert['type']) => (message: string) => {
	if (browser)
		alerts.update((a) => [...a, { id: crypto.randomUUID(), type, message, duration: 5000 }]);
};

export const success = show('success');
export const warning = show('warning');
export const error = show('error');

/** Logs `e` and shows its API detail, or `fallback` for other errors. */
export const failed = (e: unknown, fallback: string) => {
	logger.error(e);
	error(isErrorResponse(e) ? e.detail : fallback);
};

export const dismiss = (id: string) => {
	alerts.update((alerts) => alerts.filter((alert) => alert.id !== id));
};
