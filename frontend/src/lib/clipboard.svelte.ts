import { logger } from '#lib/logger.ts';

/** Copies text and reports `copied` for two seconds, for a check-mark confirmation. */
export function clipboard() {
	let copied = $state(false);
	let timer: ReturnType<typeof setTimeout> | undefined;
	return {
		get copied() {
			return copied;
		},
		async copy(text: string) {
			try {
				await navigator.clipboard.writeText(text);
			} catch (e) {
				logger.error(e);
				return;
			}
			copied = true;
			clearTimeout(timer);
			timer = setTimeout(() => (copied = false), 2000);
		}
	};
}
