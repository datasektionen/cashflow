<!--
@component
A generic single-line text input, styled to match ComboBox/AmountInput.
-->
<script lang="ts">
	import type { Snippet } from 'svelte';

	let {
		value = $bindable(''),
		name,
		type = 'text',
		placeholder = '',
		class: className = '',
		icon,
		onchange,
		onblur,
		onkeydown
	}: {
		value?: string;
		name?: string;
		type?: 'text' | 'search' | 'email';
		placeholder?: string;
		class?: string;
		icon?: Snippet;
		onchange?: (value: string) => void;
		onblur?: (e: FocusEvent) => void;
		onkeydown?: (e: KeyboardEvent) => void;
	} = $props();
</script>

<div
	class="flex w-full flex-row items-center border border-base-500 bg-base-200 dark:border-dark-base-200 dark:bg-dark-base-200 {className}"
>
	{#if icon}
		<span class="pl-2 text-base-subtle dark:text-dark-base-subtle">
			{@render icon()}
		</span>
	{/if}
	<input
		{name}
		{type}
		bind:value
		oninput={() => onchange?.(value)}
		{onblur}
		{onkeydown}
		{placeholder}
		aria-label={placeholder}
		class="w-full flex-1 border-0 bg-transparent p-2 text-sm outline-none placeholder:text-base-subtle dark:placeholder:text-dark-base-subtle"
	/>
</div>
