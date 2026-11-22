import { writable } from 'svelte/store';
import { isErrorResponse } from '#lib/api/errors.ts';
import { logger } from '#lib/logger.ts';

export type Alert = {
	id: string;
	type: 'success' | 'warning' | 'error';
	message: string;
	duration: number;
};

export const alerts = writable<Alert[]>([]);

const show = (type: Alert['type']) => (message: string) =>
	alerts.update((a) => [...a, { id: crypto.randomUUID(), type, message, duration: 5000 }]);

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
