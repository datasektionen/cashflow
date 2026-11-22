<script lang="ts">
	import type { Snippet } from 'svelte';
	import { Circle, CircleCheck } from '@lucide/svelte';

	type Props = { label: string; done?: boolean; sub?: string | null; children: Snippet };

	let { label, done, sub, children }: Props = $props();
</script>

<div class="flex min-w-0 flex-col gap-1">
	<dt class="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
		{#if done === true}
			<CircleCheck class="size-3.5 shrink-0 text-primary-text" />
		{:else if done === false}
			<Circle class="size-3.5 shrink-0" />
		{/if}
		<span class="truncate">{label}</span>
	</dt>
	<dd class="truncate text-sm font-medium">{@render children()}</dd>
	{#if sub}<dd class="truncate text-xs text-muted-foreground">{sub}</dd>{/if}
</div>
