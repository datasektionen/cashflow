import { _ } from 'svelte-i18n';
import { fromStore } from 'svelte/store';

type Result = {
	getErrors(): Record<string, string[]>;
	isTested(field: string): boolean;
	isValid(): boolean;
};

type Suite<T, R extends Result> = { get(): R; run(data: T, field?: string): R };

export function formValidation<T, R extends Result>(suite: Suite<T, R>, data: () => T) {
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
		onblur: (e: FocusEvent & { currentTarget: HTMLInputElement }) => {
			result = suite.run(data(), e.currentTarget.name);
		}
	};
}

export type FormValidation = ReturnType<typeof formValidation>;
