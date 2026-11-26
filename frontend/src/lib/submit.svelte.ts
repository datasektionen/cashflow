import { get } from 'svelte/store';
import { _ } from 'svelte-i18n';
import { goto } from '$app/navigation';
import { failed } from '#lib/stores/alerts.ts';

/**
 * Form submit handler that ignores repeat submits and shows failures.
 * The action returns where to go after saving, or nothing when it did not save.
 */
export function submitter(action: () => Promise<string | undefined>) {
	let submitting = $state(false);
	let saved = false;

	// Resolves to the action's destination when it saved
	async function save() {
		if (submitting) return;
		submitting = true;
		try {
			const to = await action();
			saved = !!to;
			return to;
		} catch (err) {
			failed(err, get(_)('action_failed'));
		} finally {
			submitting = false;
		}
	}

	return {
		get submitting() {
			return submitting;
		},
		get saved() {
			return saved;
		},
		save,
		async onsubmit(e: SubmitEvent) {
			e.preventDefault();
			const to = await save();
			if (to) await goto(to);
		}
	};
}
