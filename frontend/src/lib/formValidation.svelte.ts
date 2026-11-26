import { _ } from 'svelte-i18n';
import { fromStore } from 'svelte/store';

type Result = {
	getErrors(): Record<string, string[]>;
	isTested(field: string): boolean;
	isValid(): boolean;
};

type Suite<T, R extends Result, D> = {
	get(): R;
	run(data: T, field?: string): R;
	dump(): D;
	resume(state: D): void;
};

export function formValidation<T, R extends Result, D>(suite: Suite<T, R, D>, data: () => T) {
	const t = fromStore(_);
	let result = $state(suite.get());
	const errors = $derived(result.getErrors());

	const showErrors = (field: string) => result.isTested(field) && (errors[field]?.length ?? 0) > 0;

	return {
		showErrors,
		errorFor: (field: string) => (showErrors(field) ? t.current(errors[field][0]) : null),
		validate(field?: string) {
			result = suite.run(data(), field);
			return result.isValid();
		},
		// Checks every field without marking any as tested (runStatic does)
		canSave() {
			const state = suite.dump();
			const valid = suite.run(data()).isValid();
			suite.resume(state);
			return valid;
		},
		onblur: (e: FocusEvent & { currentTarget: HTMLInputElement }) => {
			result = suite.run(data(), e.currentTarget.name);
		}
	};
}

export type FormValidation = ReturnType<typeof formValidation>;
