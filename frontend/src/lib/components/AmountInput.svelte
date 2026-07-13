<!--
@component
A monetary amount input. Edits a raw numeric `value` (bindable) while showing a
nicely formatted display string (sv-SE, 2 decimals) when not focused. On focus it
reveals the plain number for editing; on blur it parses (accepting `,` or `.` and
spaces) and reformats. Renders an optional hidden input for native form submission.
-->
<script lang="ts">
	import { Lock } from '@lucide/svelte';

	let {
		value = $bindable(null),
		name,
		placeholder = '0,00',
		suffix = '',
		class: className = '',
		locked = false
	}: {
		value?: number | null;
		name?: string;
		placeholder?: string;
		suffix?: string;
		class?: string;
		locked?: boolean;
	} = $props();

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});

	let focused = $state(false);
	let display = $state(value != null ? fmt.format(value) : '');

	// Keep the display in sync when `value` is changed from the outside
	// (e.g. a reset), but never fight the user while they are typing.
	$effect(() => {
		if (!focused) {
			display = value != null ? fmt.format(value) : '';
		}
	});

	function onFocus() {
		focused = true;
		display = value?.toString() ?? '';
	}

	function onBlur() {
		focused = false;
		const num = parseFloat(display.replace(/\s/g, '').replace(',', '.'));
		if (!isNaN(num) && num >= 0) {
			value = num;
			display = fmt.format(num);
		} else {
			value = null;
			display = '';
		}
	}
</script>

<div class="relative flex w-full items-center">
	{#if name}<input type="hidden" {name} value={value ?? ''} />{/if}
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
