import type { Snippet } from 'svelte';

export type TableColumn<T> = {
	id: string;
	header: string;
	render?: (row: T) => string;
	renderSnippet?: Snippet<[T]>;
	width?: string;
	align?: 'right';
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
