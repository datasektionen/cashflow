import type { Snippet } from 'svelte';

export type TableColumn<T> = {
	id: string;
	key?: keyof T;
	header: string;
	render?: (row: T) => string;
	renderSnippet?: Snippet<[T]>;
	width: string;
};

export type TableRowProps<T> = {
	onClick?: (row: T) => void;
	class?: string | ((row: T) => string);
};
