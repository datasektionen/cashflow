<!--
@component
The bindable value is a dinero object.
-->
<script lang="ts">
	import { dineroFromDecimal, formatDineroAmount } from '$lib/money';
	import { Lock } from '@lucide/svelte';
	import { isZero, SEK, toDecimal, type Dinero } from 'dinero.js';

	let {
		value = $bindable(null),
		name,
		placeholder = '0,00',
		suffix = '',
		class: className = '',
		locked = false
	}: {
		value?: Dinero<number, 'SEK'> | null;
		name?: string;
		placeholder?: string;
		suffix?: string;
		class?: string;
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

	function onBlur() {
		focused = false;

		value = parse(display);
		display = isEmpty(value) ? '' : formatDineroAmount(value);
	}
</script>

<div class="relative flex w-full items-center">
	{#if name}<input type="hidden" {name} value={value != null ? toDecimal(value) : ''} />{/if}
	<input
		type="text"
		inputmode="decimal"
		bind:value={display}
		onfocus={onFocus}
		onblur={onBlur}
		disabled={locked}
		{placeholder}
		class="w-full border-0 bg-transparent p-2 text-right text-sm tabular-nums outline-none placeholder:text-base-subtle disabled:cursor-not-allowed disabled:opacity-75 dark:placeholder:text-dark-base-subtle {suffix ||
		locked
			? 'pr-12'
			: ''} {className}"
	/>
	{#if locked}
		<Lock class="pointer-events-none absolute right-3 size-3 text-gray-500" />
	{:else if suffix}
		<span
			class="pointer-events-none absolute right-3 text-sm text-base-subtle dark:text-dark-base-subtle"
		>
			{suffix}
		</span>
	{/if}
</div>
