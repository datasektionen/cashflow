<script lang="ts">
	import { Card, Skeleton } from '#lib/components/ui/index.ts';

	let { label, value }: { label: string; value?: string | number } = $props();
</script>

<Card padded={false} class="min-w-0 px-4 py-3">
	<p class="text-xs text-muted-foreground">{label}</p>
	{#if value === undefined}
		<Skeleton class="my-1 h-5 w-20" />
	{:else}
		<p class="truncate text-lg font-bold tabular-nums">{value}</p>
	{/if}
</Card>
