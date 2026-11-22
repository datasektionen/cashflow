/**
 * Tracks the latest result of a reactive promise. The previous value stays
 * available while a new one loads, so views can dim instead of flashing a skeleton.
 */
export function latest<T>(promise: () => Promise<T>) {
	const state = $state<{ value?: T; error?: unknown; loading: boolean }>({ loading: true });
	$effect(() => {
		const current = promise();
		let stale = false;
		state.loading = true;
		current.then(
			(value) => {
				if (stale) return;
				state.value = value;
				state.error = undefined;
				state.loading = false;
			},
			(error) => {
				if (stale) return;
				state.error = error;
				state.loading = false;
			}
		);
		return () => {
			stale = true;
		};
	});
	return state;
}
