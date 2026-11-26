<script lang="ts">
	import { Badge, Tooltip } from '#lib/components/ui/index.ts';

	let { parts }: { parts: { cost_centre: string }[] } = $props();

	const names = $derived([...new Set(parts.map((p) => p.cost_centre))]);
</script>

{#if names.length > 0}
	<span class="flex min-w-0 items-center gap-1">
		<Badge variant="outline" class="min-w-0 truncate" title={names[0]}>
			<span class="truncate">{names[0]}</span>
		</Badge>
		{#if names.length > 1}
			<Tooltip content={names.join(', ')}>
				{#snippet children({ props })}
					<Badge
						{...props}
						variant="neutral"
						class="shrink-0 cursor-default tabular-nums"
						tabindex={0}
					>
						+{names.length - 1}
					</Badge>
				{/snippet}
			</Tooltip>
		{/if}
	</span>
{/if}
