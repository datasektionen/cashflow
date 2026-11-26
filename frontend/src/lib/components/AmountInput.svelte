<!--
@component
The bindable value is a dinero object.
-->
<script lang="ts">
	import { cn } from 'tailwind-variants';
	import { inputShell } from './inputShell';
	import { dineroFromDecimal, formatDineroAmount } from '#lib/money.ts';
	import { Lock } from '@lucide/svelte';
	import { isZero, SEK, toDecimal, type Dinero } from 'dinero.js';

	let {
		value = $bindable(null),
		name,
		id,
		label,
		suffix = '',
		locked = false
	}: {
		value?: Dinero<number, 'SEK'> | null;
		name?: string;
		id?: string;
		label?: string;
		suffix?: string;
		locked?: boolean;
	} = $props();

	// Zero is shown as an empty field (with the placeholder) so that
	// untouched amounts don't have to be cleared before typing.
	const isEmpty = (v: Dinero<number, 'SEK'> | null): v is null => v == null || isZero(v);

	let focused = $state(false);
	let display = $state(isEmpty(value) ? '' : formatDineroAmount(value));

	function parse(input: string): Dinero<number, 'SEK'> | null {
		const normalized = input.replace(/\s/g, '').replace(',', '.');
		if (normalized === '' || normalized.startsWith('-')) return null;
		try {
			return dineroFromDecimal(normalized, SEK);
		} catch {
			return null;
		}
	}

	// Keep the display in sync when `value` is changed from the outside
	// (e.g. a reset), but never fight the user while they are typing.
	$effect(() => {
		if (!focused) {
			display = isEmpty(value) ? '' : formatDineroAmount(value);
		}
	});

	function onFocus() {
		focused = true;
		display = isEmpty(value) ? '' : toDecimal(value);
	}

	// The value follows typing (so Enter submits it); blur also tidies the display
	function onBlur() {
		focused = false;

		value = parse(display);
		display = isEmpty(value) ? '' : formatDineroAmount(value);
	}
</script>

<div class={cn(inputShell, 'relative', locked && 'bg-muted')}>
	{#if name}<input type="hidden" {name} value={value != null ? toDecimal(value) : ''} />{/if}
	<input
		{id}
		aria-label={label}
		type="text"
		inputmode="decimal"
		bind:value={display}
		oninput={() => (value = parse(display))}
		onfocus={onFocus}
		onblur={onBlur}
		disabled={locked}
		placeholder="0,00"
		class={cn(
			'h-full w-full min-w-0 bg-transparent px-3 py-2 text-right text-sm tabular-nums outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-60',
			(suffix || locked) && 'pr-12'
		)}
	/>
	{#if locked}
		<Lock class="pointer-events-none absolute right-3 size-3.5 text-muted-foreground" />
	{:else if suffix}
		<span class="pointer-events-none absolute right-3 text-sm text-muted-foreground">
			{suffix}
		</span>
	{/if}
</div>
