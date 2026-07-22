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

export const success = (message: string, duration: number = 5000): Alert => {
	return {
		id: crypto.randomUUID(),
		type: AlertType.Success,
		message,
		duration
	};
};

export const warning = (message: string, duration: number = 5000): Alert => ({
	id: crypto.randomUUID(),
	type: AlertType.Warning,
	message,
	duration
});

export const info = (message: string, duration: number = 5000): Alert => ({
	id: crypto.randomUUID(),
	type: AlertType.Info,
	message,
	duration
});

export const alerts: Writable<Alert[]> = writable<Alert[]>([]);

export const dismiss = (id: string) => {
	alerts.update((alerts) => alerts.filter((alert) => alert.id !== id));
};
