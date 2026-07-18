<!--
@component
A generic checkbox, styled like the selection checkboxes on the payment page.
Optionally renders a label and supports an indeterminate state.
-->
<script lang="ts">
	import { Checkbox } from 'bits-ui';
	import { Check, Minus } from '@lucide/svelte';
	import type { Snippet } from 'svelte';

	let {
		checked = $bindable(false),
		indeterminate = false,
		name,
		disabled = false,
		class: className = '',
		onCheckedChange,
		children
	}: {
		checked?: boolean;
		indeterminate?: boolean;
		name?: string;
		disabled?: boolean;
		class?: string;
		onCheckedChange?: (checked: boolean) => void;
		children?: Snippet;
	} = $props();
</script>

{#snippet box()}
	<Checkbox.Root
		bind:checked
		{indeterminate}
		{name}
		{disabled}
		onCheckedChange={(v) => onCheckedChange?.(!!v)}
		class={[
			'flex size-4 shrink-0 cursor-pointer items-center justify-center border border-base-800 bg-base-500 inset-shadow-xs',
			'data-[state=checked]:border-money-green-500 data-[state=checked]:bg-money-green-500',
			'data-[state=indeterminate]:border-money-green-500 data-[state=indeterminate]:bg-money-green-500',
			'dark:border-dark-base-50 dark:bg-dark-base-200',
			'disabled:cursor-not-allowed disabled:opacity-50',
			className
		]}
	>
		{#snippet children({ checked, indeterminate })}
			{#if indeterminate}
				<Minus class="size-3 text-white" />
			{:else if checked}
				<Check class="size-3 text-white" />
			{/if}
		{/snippet}
	</Checkbox.Root>
{/snippet}

{#if children}
	<label
		class="flex cursor-pointer items-center gap-x-2 text-sm text-base-subtle dark:text-dark-base-subtle"
	>
		{@render children()}
		{@render box()}
	</label>
{:else}
	{@render box()}
{/if}
