<script lang="ts">
	import { Tooltip as TooltipPrimitive } from 'bits-ui';
	import type { Snippet } from 'svelte';

	type Props = {
		content: string;
		children: Snippet<[{ props: Record<string, unknown> }]>;
	};

	let { content, children }: Props = $props();
</script>

<TooltipPrimitive.Root delayDuration={300}>
	<TooltipPrimitive.Trigger>
		{#snippet child({ props })}
			{@render children({ props })}
		{/snippet}
	</TooltipPrimitive.Trigger>
	<TooltipPrimitive.Portal>
		<TooltipPrimitive.Content
			sideOffset={6}
			class="z-50 bg-foreground px-2 py-1 text-xs text-background shadow-md"
		>
			{content}
		</TooltipPrimitive.Content>
	</TooltipPrimitive.Portal>
</TooltipPrimitive.Root>
