<script lang="ts">
	import type { Snippet } from 'svelte';
	import { cn } from 'tailwind-variants';

	type Props = {
		title: string;
		description?: string;
		class?: string;
		children: Snippet;
	};

	let { title, description, class: className, children }: Props = $props();
</script>

<section class={cn('flex flex-col gap-4', className)}>
	<div class="flex flex-wrap items-end justify-between gap-3">
		<div class="flex flex-col gap-1">
			<h2 class="text-lg font-bold tracking-tight">{title}</h2>
			{#if description}<p class="text-sm text-muted-foreground">{description}</p>{/if}
		</div>
	</div>
	{@render children()}
</section>
