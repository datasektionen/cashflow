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
	// When set, the row's first cell renders a stretched link covering the whole
	// row, giving native "open in new tab" support (middle/⌘-click, etc.).
	href?: (row: T) => string;
	class?: string | ((row: T) => string);
};
