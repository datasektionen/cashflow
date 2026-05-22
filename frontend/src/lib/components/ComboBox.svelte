<!--
@component
A combobox (mix between select and text input) for selecting from a list of options.
Wraps bits-ui's Combobox component. Supports fuzzy text search using fuse.js.
-->
<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { ChevronDown, ChevronsUpDown, ChevronUp } from '@lucide/svelte';
	import { Combobox } from 'bits-ui';
	import Fuse from 'fuse.js';

	let {
		name,
		items,
		placeholder = '',
		value = $bindable(''),
		onblur
	}: {
		name: string;
		items: string[];
		placeholder?: string;
		value?: string;
		onblur?: (e: FocusEvent) => void;
	} = $props();

	let searchValue = $state('');
	let open = $state(false);

	const fuse = $derived(new Fuse(items));
	let filtered = $derived(fuse.search(searchValue));
</script>

<Combobox.Root type="single" {name} bind:value bind:open inputValue={searchValue}>
	<div class="relative">
		<div class="flex flex-row">
			<Combobox.Input
				class="p-2 placeholder:text-sm placeholder:text-base-subtle dark:placeholder:text-dark-base-subtle"
				oninput={(e) => (searchValue = e.currentTarget.value)}
				onkeydown={(e) => {
					if (e.key === 'Tab' && searchValue !== '') {
						value = filtered[0] ? filtered[0].item : '';
						searchValue = filtered[0] ? filtered[0].item : searchValue;
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
			<Combobox.Trigger>
				<ChevronsUpDown />
			</Combobox.Trigger>
		</div>

		<Combobox.Portal>
			<Combobox.Content
				sideOffset={10}
				class="focus-override border-muted h-96 w-full border-2 border-base-300 bg-base-200 dark:border-dark-base-300 dark:bg-dark-base-200"
			>
				<Combobox.ScrollUpButton class="p-2 text-base dark:text-dark-base-text">
					<ChevronUp class="m-auto" />
				</Combobox.ScrollUpButton>
				<Combobox.Viewport class="w-full p-2">
					{#each filtered.map((it) => it.item) as item}
						<Combobox.Item
							class="cursor-pointer p-2 text-base-text data-highlighted:bg-base-300 dark:text-dark-base-text dark:data-highlighted:bg-dark-base-300"
							value={item}
							label={item}>{item}</Combobox.Item
						>
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
