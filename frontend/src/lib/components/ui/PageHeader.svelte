<script lang="ts">
	import type { Snippet } from 'svelte';
	import { cn } from 'tailwind-variants';

	type Props = {
		title?: string | null;
		heading?: Snippet;
		// Smaller title for claim descriptions, which can be long
		small?: boolean;
		class?: string;
	};

	let { title, heading, small = false, class: className }: Props = $props();
</script>

<header class={cn('flex flex-wrap items-end justify-between gap-4 pb-6', className)}>
	<div class="flex min-w-0 flex-col gap-1">
		<h1 class={['font-bold tracking-tight wrap-break-word', small ? 'text-2xl' : 'text-3xl']}>
			{#if heading}{@render heading()}{:else}{title}{/if}
		</h1>
	</div>
</header>
