<script lang="ts">
	import { Card, Skeleton } from '#lib/components/ui/index.ts';
	import { getPreferences } from '#lib/preferences.svelte.ts';

	const prefs = getPreferences();
</script>

{#snippet header(width: string)}
	<div class="border-b border-border px-5 py-3.5"><Skeleton class="h-5 {width}" /></div>
{/snippet}

<div
	style:--receipt-width="{prefs.receiptWidth}%"
	class={[
		'grid grid-cols-1 gap-6',
		prefs.receiptWidth > 0 && 'lg:grid-cols-[minmax(0,1fr)_var(--receipt-width)] lg:items-start'
	]}
>
	<div class="flex flex-col gap-6">
		<Skeleton class="h-9 w-2/3" />
		<div class="flex items-start justify-between gap-3">
			<div class="flex flex-1 flex-wrap items-center gap-1.5">
				{#each ['w-20', 'w-28', 'w-36', 'w-24', 'w-24', 'w-24'] as width, i (i)}
					<Skeleton class="h-7 {width}" />
				{/each}
			</div>
		</div>
		<Card padded={false}>
			{@render header('w-32')}
			<div class="flex flex-col divide-y divide-border">
				{#each { length: 3 }, i (i)}
					<div class="flex h-12 items-center justify-between gap-4 px-3">
						<Skeleton class="h-4 w-2/5" />
						<Skeleton class="h-4 w-20" />
					</div>
				{/each}
			</div>
		</Card>
		<Card padded={false} class="divide-y divide-border">
			{#each [4, 3] as count, i (i)}
				<div class="grid grid-cols-2 gap-x-6 gap-y-4 px-5 py-4 sm:auto-cols-fr sm:grid-flow-col">
					{#each { length: count }, j (j)}
						<div class="flex flex-col gap-1.5">
							<Skeleton class="h-3 w-16" />
							<Skeleton class="h-5 w-24" />
						</div>
					{/each}
				</div>
			{/each}
		</Card>
		<Card padded={false}>
			{@render header('w-28')}
			<div class="h-24"></div>
		</Card>
	</div>
	{#if prefs.receiptWidth > 0}
		<div
			class="flex h-[70dvh] flex-col border border-border bg-card max-lg:order-first lg:sticky lg:top-6 lg:h-[calc(100dvh-7rem)]"
		>
			<div class="flex justify-end gap-2 border-b border-border p-3">
				<Skeleton class="size-9" />
				<Skeleton class="h-9 w-24" />
				<Skeleton class="h-9 w-28" />
			</div>
			<Skeleton class="m-3 flex-1" />
		</div>
	{/if}
</div>
