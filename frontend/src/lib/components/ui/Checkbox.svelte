<script lang="ts">
	import { Checkbox as CheckboxPrimitive } from 'bits-ui';
	import { Check, Minus } from '@lucide/svelte';
	import type { Snippet } from 'svelte';
	import { cn } from 'tailwind-variants';

	type Props = Omit<CheckboxPrimitive.RootProps, 'children'> & { children?: Snippet };

	let {
		checked = $bindable(false),
		indeterminate = $bindable(false),
		ref = $bindable(null),
		class: className,
		children,
		...rest
	}: Props = $props();
</script>

{#snippet box()}
	<CheckboxPrimitive.Root
		bind:ref
		bind:checked
		bind:indeterminate
		class={cn(
			'peer flex size-4 shrink-0 cursor-pointer items-center justify-center border border-input bg-card text-primary-foreground transition-colors data-disabled:cursor-not-allowed data-disabled:opacity-50 data-[state=checked]:border-primary data-[state=checked]:bg-primary data-[state=indeterminate]:border-primary data-[state=indeterminate]:bg-primary',
			className as string
		)}
		{...rest}
	>
		{#snippet children({ checked, indeterminate })}
			{#if indeterminate}
				<Minus class="size-3" strokeWidth={3} />
			{:else if checked}
				<Check class="size-3" strokeWidth={3} />
			{/if}
		{/snippet}
	</CheckboxPrimitive.Root>
{/snippet}

{#if children}
	<label class="inline-flex cursor-pointer items-center gap-2 text-sm">
		{@render box()}
		{@render children()}
	</label>
{:else}
	{@render box()}
{/if}
