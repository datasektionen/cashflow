import type { Snippet } from 'svelte';
import type { Payment } from '#lib/api/types.ts';

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
	// When both are set, a plain click calls onClick and href is used for
	// middle-click / Ctrl/Cmd/Shift-click (open in new tab).
	onClick?: (row: T) => void;
	href?: (row: T) => string;
	class?: string | ((row: T) => string);
	expandedSnippet?: Snippet<[x: T]>;
};
