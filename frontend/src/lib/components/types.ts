import type { Snippet } from 'svelte';
import type { Payment } from '$lib/api/types';

export type TableColumn<T> = {
	id: string;
	key?: keyof T;
	header: string;
	render?: (row: T) => string;
	renderSnippet?: Snippet<[T]>;
	width: string;
	sorting?: string[];
};

export type TableRowProps<T> = {
	onClick?: (row: T) => void;
	href?: (row: T) => string;
	class?: string | ((row: T) => string);
	expandedSnippet?: Snippet<[x: T]>;
};
