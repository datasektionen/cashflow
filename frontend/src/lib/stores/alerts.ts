import { type Writable, writable } from 'svelte/store';

export enum AlertType {
	Success = 'success',
	Error = 'error',
	Info = 'info',
	Warning = 'warning'
}

export type Alert = {
	id: string;
	type: AlertType;
	message: string;
	duration: number;
};

export const error = (message: string, duration: number = 5000): Alert => {
	return {
		id: crypto.randomUUID(),
		type: AlertType.Error,
		message,
		duration
	};
};

export const alerts: Writable<Alert[]> = writable<Alert[]>([]);

export const dismiss = (id: string) => {
	alerts.update((alerts) => alerts.filter((alert) => alert.id !== id));
};
