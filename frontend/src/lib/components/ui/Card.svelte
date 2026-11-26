<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	type Props = HTMLAttributes<HTMLDivElement> & {
		title?: string;
		description?: string;
		actions?: Snippet;
		padded?: boolean;
	};

	let {
		title,
		description,
		actions,
		padded = true,
		class: className,
		children,
		...rest
	}: Props = $props();
</script>

<div class={cn('border border-border bg-card', className as string)} {...rest}>
	{#if title || actions}
		<div class="flex items-start justify-between gap-4 border-border px-5 py-3 not-last:border-b">
			<div class="flex flex-col gap-1">
				{#if title}<h2 class="text-base font-bold">{title}</h2>{/if}
				{#if description}<p class="text-sm text-muted-foreground">{description}</p>{/if}
			</div>
			<!-- Kept to the title's line height so headers with buttons are no taller -->
			{#if actions}<div class="-my-1 flex shrink-0 items-center gap-2">
					{@render actions()}
				</div>{/if}
		</div>
	{/if}
	{#if padded}
		<div class="p-5">{@render children?.()}</div>
	{:else}
		{@render children?.()}
	{/if}
</div>
