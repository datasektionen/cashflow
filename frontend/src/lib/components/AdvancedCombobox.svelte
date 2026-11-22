<script lang="ts" module>
	import type { Snippet } from 'svelte';

	export type ComboboxColumn<T> = {
		field: keyof T;
		render: Snippet<[T]>;
	};

	type AdvancedComboboxProps<T> = {
		name: string;
		items: T[];
		searchField: (keyof T)[];
		valueField: keyof T;
		columns: ComboboxColumn<T>[];
		display?: Snippet<[T]>;
		value?: string;
		placeholder?: string;
		label?: string;
		class?: string;
		locked?: boolean;
		clearable?: boolean;
		onchange?: (value: string | null) => void;
	};
</script>

<script lang="ts" generics="T">
	import { Combobox } from '#lib/components/ui/index.ts';

	let {
		name,
		items,
		searchField,
		valueField,
		columns,
		display,
		value = $bindable(''),
		placeholder = '',
		label,
		class: className = '',
		locked = false,
		clearable = false,
		onchange
	}: AdvancedComboboxProps<T> = $props();
</script>

{#snippet row(item: T)}
	<span class="grid min-w-0 flex-1 grid-cols-[4.5rem_minmax(0,1fr)] items-baseline gap-3">
		{#each columns as column (column.field)}
			<span class="truncate first:font-mono first:tabular-nums">{@render column.render(item)}</span>
		{/each}
	</span>
{/snippet}

<Combobox
	{name}
	{items}
	getValue={(item) => String(item[valueField])}
	getSearchText={(item) => searchField.map((f) => String(item[f])).join(' ')}
	bind:value
	{placeholder}
	{label}
	{locked}
	{clearable}
	{display}
	onchange={(v) => onchange?.(v || null)}
	item={row}
	contentClass="min-w-80"
	class={className}
/>
