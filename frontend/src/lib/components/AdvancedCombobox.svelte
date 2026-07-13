<!--
@component
A combobox (mix between select and text input) for selecting from a list of options.
Wraps bits-ui's Combobox component. Supports fuzzy text search using fuse.js.

bits-ui's Combobox is string-valued, so the selected `value` is a string taken from
`valueField` of the chosen item (e.g. an Account's `code`). Use `searchField` for the
field to fuzzy-search, and the `display` snippet to render the resolved item when collapsed.
-->
<script lang="ts" module>
	import type { Snippet } from 'svelte';

	export type ComboboxColumn<T> = {
		label: string;
		field: keyof T;
		render: Snippet<[T]>;
	};

	export type AdvancedComboboxProps<T> = {
		name: string;
		items: T[];
		searchField: keyof T | (keyof T)[];
		valueField: keyof T;
		columns: ComboboxColumn<T>[];
		display?: Snippet<[T]>;
		value?: string;
		placeholder?: string;
		class?: string;
		onchange?: (value: string | null) => void;
		onblur?: (e: FocusEvent) => void;
	};
</script>

<script lang="ts" generics="T">
	import { _ } from 'svelte-i18n';
	import { ChevronDown, ChevronsUpDown, ChevronUp } from '@lucide/svelte';
	import { Combobox } from 'bits-ui';
	import Fuse from 'fuse.js';

	let {
		name,
		items,
		searchField,
		valueField,
		columns,
		display,
		value = $bindable(''),
		placeholder = '',
		class: className = '',
		onchange,
		onblur
	}: AdvancedComboboxProps<T> = $props();

	const keyOf = (item: T): string => String(item[valueField]);

	let searchValue = $state(value);
	let open = $state(false);

	const fuse = $derived(
		new Fuse(items, {
			keys: (Array.isArray(searchField) ? searchField : [searchField]).map((f) => ({
				name: String(f),
				getFn: (item: T) => String(item[f])
			}))
		})
	);

	let filtered = $derived(
		searchValue ? fuse.search(searchValue) : items.map((item, i) => ({ item, refIndex: i }))
	);

	const selected = $derived(items.find((it) => keyOf(it) === value) ?? null);

	const showDisplay = $derived(display != null && selected != null && !open);

	function commit(v: string) {
		value = v;
		searchValue = v;
		onchange?.(v || null);
	}
</script>

<Combobox.Root
	type="single"
	{name}
	{value}
	bind:open
	inputValue={searchValue}
	onValueChange={(v) => commit(v ?? '')}
>
	<div class="relative w-full">
		<div
			class="flex w-full flex-row border border-base-500 bg-base-200 dark:border-dark-base-200 dark:bg-dark-base-200 {className}"
		>
			<div class="relative flex-1">
				<Combobox.Input
					class="w-full p-2 placeholder:text-sm placeholder:text-base-subtle dark:placeholder:text-dark-base-subtle {showDisplay
						? 'text-transparent'
						: ''}"
					onclick={() => (open = true)}
					oninput={(e) => {
						searchValue = e.currentTarget.value;
						if (!searchValue) commit('');
					}}
					onkeydown={(e) => {
						if (e.key === 'Tab' && searchValue !== '') {
							commit(filtered[0] ? keyOf(filtered[0].item) : '');
						}
					}}
					onblur={(e) => {
						setTimeout(() => {
							if (!open) onblur?.(e);
						}, 0);
					}}
					{placeholder}
					aria-label={placeholder}
				></Combobox.Input>
				{#if showDisplay && selected}
					<div class="pointer-events-none absolute inset-0 flex items-center p-2">
						{@render display!(selected)}
					</div>
				{/if}
			</div>
			<Combobox.Trigger>
				<ChevronsUpDown />
			</Combobox.Trigger>
		</div>

		<Combobox.Portal>
			<Combobox.Content
				sideOffset={10}
				class="focus-override border-muted max-h-[min(24rem,var(--bits-combobox-content-available-height))] w-(--bits-combobox-anchor-width) border-2 border-base-300 bg-base-200 dark:border-dark-base-300 dark:bg-dark-base-200"
			>
				<Combobox.ScrollUpButton class="p-2 text-base dark:text-dark-base-text">
					<ChevronUp class="m-auto" />
				</Combobox.ScrollUpButton>
				<Combobox.Viewport class="w-full p-2">
					{#each filtered.map((it) => it.item) as item}
						<Combobox.Item
							class="cursor-pointer p-2 text-base-text data-highlighted:bg-base-300 dark:text-dark-base-text dark:data-highlighted:bg-dark-base-300"
							value={keyOf(item)}
						>
							<div class="flex flex-row gap-x-3">
								{#each columns as column}
									<span>{@render column.render(item)}</span>
								{/each}
							</div>
						</Combobox.Item>
					{:else}
						<span class="block px-5 py-2 text-sm text-base-subtle dark:text-dark-base-subtle">
							{$_('no_results')}
						</span>
					{/each}
				</Combobox.Viewport>
				<Combobox.ScrollDownButton class="p-2 text-base-text dark:text-dark-base-text">
					<ChevronDown class="m-auto" />
				</Combobox.ScrollDownButton>
			</Combobox.Content>
		</Combobox.Portal>
	</div>
</Combobox.Root>
