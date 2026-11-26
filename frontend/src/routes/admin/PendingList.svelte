<script lang="ts">
	import { Badge } from '#lib/components/ui/index.ts';

	let {
		rows,
		emptyText
	}: {
		rows: { label: string; href: string; count: number }[];
		emptyText: string;
	} = $props();
</script>

{#if rows.length === 0}
	<p class="px-5 py-6 text-center text-sm text-muted-foreground">{emptyText}</p>
{:else}
	<ul class="max-h-80 divide-y divide-border overflow-y-auto">
		{#each rows as row (row.href)}
			<li>
				<a
					href={row.href}
					class="flex items-center justify-between gap-2 px-5 py-2.5 text-sm transition-colors hover:bg-muted/50"
				>
					<span class="truncate">{row.label}</span>
					<Badge variant="success" class="tabular-nums">
						{row.count < 100 ? row.count : '99+'}
					</Badge>
				</a>
			</li>
		{/each}
	</ul>
{/if}
