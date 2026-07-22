<!--
@component
A combobox (mix between select and text input) for selecting from a list of options.
Wraps bits-ui's Combobox component. Supports fuzzy text search using fuse.js.
-->
<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { ChevronDown, ChevronsUpDown, ChevronUp, Lock } from '@lucide/svelte';
	import { Combobox } from 'bits-ui';
	import Fuse from 'fuse.js';

	let {
		name,
		items,
		placeholder = '',
		value = $bindable(''),
		searchValue = $bindable(''),
		class: className = '',
		locked = false,
		onchange,
		onblur
	}: {
		name: string;
		items: string[];
		placeholder?: string;
		value?: string;
		searchValue?: string;
		class?: string;
		locked?: boolean;
		onchange?: (value: string) => void;
		onblur?: (e: FocusEvent) => void;
	} = $props();

	// let searchValue = $state(value ?? '');
	let open = $state(false);

	const fuse = $derived(new Fuse(items));
	let filtered = $derived(
		searchValue ? fuse.search(searchValue) : items.map((item, i) => ({ item, refIndex: i }))
	);
</script>

<Combobox.Root
	type="single"
	{name}
	bind:value
	bind:open
	disabled={locked}
	inputValue={searchValue}
	onValueChange={(v) => onchange?.(v ?? '')}
>
	<div class="relative w-full">
		<div
			class="flex w-full flex-row border border-base-500 bg-base-200 dark:border-dark-base-200 dark:bg-dark-base-200 {locked
				? 'cursor-not-allowed opacity-75'
				: ''} {className}"
		>
			<Combobox.Input
				class="w-full flex-1 p-2 placeholder:text-sm placeholder:text-base-subtle disabled:cursor-not-allowed dark:placeholder:text-dark-base-subtle"
				onclick={() => (open = true)}
				oninput={(e) => {
					searchValue = e.currentTarget.value;
					if (!searchValue) {
						value = '';
						onchange?.('');
					}
				}}
				onkeydown={(e) => {
					if (e.key === 'Tab' && searchValue !== '') {
						const completed = filtered[0] ? filtered[0].item : '';
						value = completed;
						searchValue = completed || searchValue;
						onchange?.(completed);
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
			<Combobox.Trigger class={locked ? 'cursor-not-allowed' : ''}>
				{#if locked}
					<Lock class="size-3 text-gray-500" />
				{:else}
					<ChevronsUpDown />
				{/if}
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
