<!--
@component
Search, highlight, then commit with Enter or Tab. Escape and blur restore the last value.
-->
<script lang="ts" generics="T">
	import { Combobox } from 'bits-ui';
	import { Check, ChevronsUpDown, Lock } from '@lucide/svelte';
	import { untrack, type Snippet } from 'svelte';
	import { _ } from 'svelte-i18n';
	import { cn } from 'tailwind-variants';
	import { rankOptions } from '#lib/search.ts';
	import Skeleton from './Skeleton.svelte';
	import { menuItem, surface } from './styles';

	type Props = {
		items: T[];
		/** Defaults to the item itself, for string items */
		getValue?: (item: T) => string;
		getLabel?: (item: T) => string;
		getSearchText?: (item: T) => string;
		value?: string;
		name?: string;
		id?: string;
		placeholder?: string;
		label?: string;
		locked?: boolean;
		/** Optional fields stay empty when merely tabbed through */
		clearable?: boolean;
		loading?: boolean;
		invalid?: boolean;
		class?: string;
		contentClass?: string;
		item?: Snippet<[T]>;
		display?: Snippet<[T]>;
		onchange?: (value: string) => void;
		onblur?: (e: FocusEvent) => void;
	};

	let {
		items,
		getValue = (item) => item as string,
		getLabel = getValue,
		getSearchText = getLabel,
		value = $bindable(''),
		name,
		id,
		placeholder = '',
		label,
		locked = false,
		clearable = false,
		loading = false,
		invalid = false,
		class: className,
		contentClass,
		item: itemSnippet,
		display,
		onchange,
		onblur
	}: Props = $props();

	let open = $state(false);
	let edited = $state(false);
	let navigated = $state(false);
	let highlighted = $state<string | null>(null);
	let input = $state<HTMLInputElement | null>(null);
	let anchor = $state<HTMLElement | null>(null);

	const selected = $derived(items.find((it) => getValue(it) === value));
	const textOf = (v: string) => {
		const match = items.find((it) => getValue(it) === v);
		return match ? getLabel(match) : v;
	};

	let query = $state('');
	$effect.pre(() => {
		const current = value;
		untrack(() => {
			query = textOf(current);
			edited = false;
		});
	});

	const filtered = $derived(edited ? rankOptions(items, query, getSearchText) : items);
	const fallback = $derived(
		(edited ? !!query.trim() : !value && !clearable) ? filtered[0] : undefined
	);

	function commit(next: string) {
		if (next !== value) {
			value = next;
			onchange?.(next);
		}
		query = textOf(next);
		edited = false;
		open = false;
	}

	function restore() {
		query = textOf(value);
		edited = false;
		navigated = false;
		open = false;
	}

	function settle(fromKey = false) {
		if (edited && !query.trim()) commit('');
		else if (navigated && highlighted !== null) commit(highlighted);
		else if (fallback && (edited || fromKey)) commit(getValue(fallback));
		else restore();
	}

	function onkeydown(e: KeyboardEvent) {
		if (e.isComposing || e.altKey || e.ctrlKey || e.metaKey) return;
		if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
			navigated = true;
			open = true;
		} else if (e.key === 'Escape' && open) {
			e.stopPropagation();
			restore();
		} else if (e.key === 'Enter' && open) {
			if (highlighted === null) {
				e.preventDefault();
				settle(true);
			}
		} else if (e.key === 'Tab' && !e.shiftKey && open) {
			settle(true);
		}
	}
</script>

<Combobox.Root
	type="single"
	{name}
	{value}
	allowDeselect={false}
	bind:open={
		() => open,
		(next) => {
			if (next) open = true;
			else restore();
		}
	}
	disabled={locked}
	inputValue={query}
	onValueChange={(v) => commit(v ?? '')}
>
	<div
		bind:this={anchor}
		class={cn(
			'relative flex h-9 w-full min-w-0 items-center border bg-card text-sm transition-colors ring-inset focus-within:border-primary focus-within:ring-1 focus-within:ring-primary',
			invalid ? 'border-danger' : 'border-input',
			locked && 'cursor-not-allowed bg-muted text-muted-foreground',
			className
		)}
	>
		<Combobox.Input
			bind:ref={input}
			{id}
			{placeholder}
			aria-label={label ?? (placeholder || undefined)}
			aria-invalid={invalid || undefined}
			class={[
				'h-full w-full min-w-0 flex-1 bg-transparent pr-8 pl-3 outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed',
				display && selected && !open && 'text-transparent'
			]}
			onfocus={() => {
				if (locked) return;
				open = true;
				input?.select();
			}}
			onclick={() => {
				if (locked || open) return;
				open = true;
				input?.select();
			}}
			oninput={(e) => {
				query = e.currentTarget.value;
				edited = true;
				navigated = false;
				open = true;
			}}
			{onkeydown}
			onblur={(e) => {
				if (open || edited) settle();
				onblur?.(e);
			}}
		/>
		{#if display && selected && !open}
			<div
				class="pointer-events-none absolute inset-y-0 right-8 left-0 flex items-center truncate px-3"
			>
				{@render display(selected)}
			</div>
		{/if}
		<!-- Clicks fall through to the input, which opens the list -->
		<span class="pointer-events-none absolute right-2.5 text-muted-foreground">
			{#if locked}<Lock class="size-3.5" />{:else}<ChevronsUpDown class="size-4" />{/if}
		</span>
	</div>

	<Combobox.Portal>
		<Combobox.Content
			customAnchor={anchor}
			sideOffset={4}
			class={cn(
				surface,
				'flex max-h-[min(15rem,var(--bits-combobox-content-available-height))] w-(--bits-combobox-anchor-width) flex-col p-0',
				contentClass
			)}
		>
			{#if loading}
				<div class="flex flex-col gap-2.5 p-3">
					{#each ['w-2/5', 'w-3/5', 'w-4/5', 'w-1/2'] as width, i (i)}
						<Skeleton class="h-4 {width}" />
					{/each}
				</div>
			{:else}
				<Combobox.Viewport class="p-1">
					{#each filtered as option, i (getValue(option))}
						{@const optionValue = getValue(option)}
						<Combobox.Item
							value={optionValue}
							label={getLabel(option)}
							onHighlight={() => (highlighted = optionValue)}
							onUnhighlight={() => {
								if (highlighted === optionValue) highlighted = null;
							}}
							class={cn(
								menuItem,
								'pr-8',
								i === 0 && highlighted === null && fallback && 'bg-muted'
							)}
						>
							{#if itemSnippet}
								{@render itemSnippet(option)}
							{:else}
								<span class="truncate">{getLabel(option)}</span>
							{/if}
							{#if optionValue === value}
								<Check class="absolute right-2 text-primary-text" />
							{/if}
						</Combobox.Item>
					{:else}
						<p class="px-2 py-3 text-center text-sm text-muted-foreground">
							{$_('no_results')}
						</p>
					{/each}
				</Combobox.Viewport>
			{/if}
		</Combobox.Content>
	</Combobox.Portal>
</Combobox.Root>
