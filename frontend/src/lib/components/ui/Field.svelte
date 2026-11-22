<script lang="ts">
	import type { Snippet } from 'svelte';
	import { cn } from 'tailwind-variants';

	type Props = {
		label?: string;
		for?: string;
		help?: string;
		error?: string | null;
		class?: string;
		children: Snippet;
	};

	let { label, for: id, help, error, class: className, children }: Props = $props();
</script>

<div class={cn('flex flex-col gap-2', className)}>
	{#if label}
		<label for={id} class="text-sm leading-none font-medium select-none">{label}</label>
	{/if}
	{@render children()}
	{#if error}
		<p role="alert" class="text-xs font-medium text-danger">{error}</p>
	{:else if help}
		<p class="text-xs text-muted-foreground">{help}</p>
	{/if}
</div>
