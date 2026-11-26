<script lang="ts">
	import type { Component } from 'svelte';
	import { cn } from 'tailwind-variants';

	type Props = {
		title: string;
		icon?: Component;
		class?: string;
	};

	let { title, icon: Icon, class: className }: Props = $props();
</script>

<div
	class={cn(
		'flex flex-col items-center justify-center gap-2 border-2 border-dashed border-border px-6 py-12 text-center',
		className
	)}
>
	{#if Icon}
		<div class="mb-1 flex size-10 items-center justify-center bg-muted">
			<Icon class="size-5 text-muted-foreground" />
		</div>
	{/if}
	<p class="text-sm font-semibold">{title}</p>
</div>
