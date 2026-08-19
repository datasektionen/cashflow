<script lang="ts">
	let {
		rows,
		emptyText
	}: {
		rows: { label: string; href: string; count: number }[];
		emptyText: string;
	} = $props();
</script>

{#if rows.length === 0}
	<p
		class="border border-base-500 px-3 py-4 text-center text-sm text-base-subtle dark:border-dark-base-200 dark:text-dark-base-subtle"
	>
		{emptyText}
	</p>
{:else}
	<ul class="max-h-80 overflow-y-auto border border-base-500 dark:border-dark-base-200">
		{#each rows as row (row.href)}
			<li>
				<a
					href={row.href}
					class="flex items-center justify-between gap-2 px-3 py-2 text-sm text-base-subtle transition-colors hover:bg-base-300 hover:text-base-text dark:text-dark-base-subtle dark:hover:bg-dark-base-200 dark:hover:text-dark-base-text"
				>
					<span>{row.label}</span>
					<span
						class="rounded-full bg-money-green-600/15 px-1.5 py-0.5 text-xs font-medium text-money-green-700 dark:bg-money-green-600/20 dark:text-money-green-400"
					>
						{row.count < 100 ? row.count : '99+'}
					</span>
				</a>
			</li>
		{/each}
	</ul>
{/if}
