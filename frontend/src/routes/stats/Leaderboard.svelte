<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { page } from '$app/state';
	import { api } from '#lib/api/index.ts';
	import type { LeaderboardEntry } from '#lib/api/types.ts';
	import UserAvatar from '#lib/components/UserAvatar.svelte';
	import { Card, Skeleton, Table } from '#lib/components/ui/index.ts';
	import RangeControl, { rangeStart } from './RangeControl.svelte';
	import { latest } from '#lib/latest.svelte.ts';

	type Props = {
		title: string;
		help: string;
		valueLabel: string;
		ordering?: '-expense_total' | '-expense_count';
		value: (entry: LeaderboardEntry) => string | number;
	};

	let { title, help, valueLabel, ordering, value }: Props = $props();

	let range = $state(0);

	const leaderboard = latest(() =>
		api.stats.leaderboard(1, 20, rangeStart(range), undefined, ordering)
	);

	const medals = [
		'bg-warning-soft text-warning-soft-foreground ring-1 ring-warning-soft-foreground/30',
		'bg-muted text-foreground ring-1 ring-border',
		'bg-danger-soft text-danger-soft-foreground ring-1 ring-danger-soft-foreground/30'
	];
	const res = $derived(leaderboard.error ? undefined : leaderboard.value);
</script>

<Card padded={false} class="flex h-full flex-col">
	<div class="flex flex-col gap-3 border-b border-border px-5 py-4">
		<div class="flex flex-col gap-1">
			<h2 class="text-base font-bold">{title}</h2>
			<p class="min-h-[2lh] text-sm text-muted-foreground">{help}</p>
		</div>
		<RangeControl bind:range />
	</div>
	<Table.Root class={['transition-opacity', leaderboard.loading && res && 'opacity-60']}>
		<Table.Header>
			<Table.Row>
				<Table.Head align="center" class="w-16">{$_('leaderboard.position')}</Table.Head>
				<Table.Head></Table.Head>
				<Table.Head align="right" class="pr-5">{valueLabel}</Table.Head>
			</Table.Row>
		</Table.Header>
		<Table.Body>
			{#if leaderboard.error}
				<Table.Row>
					<Table.Cell colspan={3} class="py-6 text-center text-sm text-danger-text">
						{$_('claims.error')}
					</Table.Cell>
				</Table.Row>
			{:else if !res}
				{#each { length: 20 }, i (i)}
					<Table.Row class="h-12">
						<Table.Cell><Skeleton class="mx-auto size-5" /></Table.Cell>
						<Table.Cell>
							<div class="flex items-center gap-3">
								<Skeleton class="size-8" />
								<Skeleton class="h-4 {i < 3 ? 'w-40' : 'w-28'}" />
							</div>
						</Table.Cell>
						<Table.Cell class="pr-5"><Skeleton class="ml-auto h-4 w-16" /></Table.Cell>
					</Table.Row>
				{/each}
			{/if}
			{#each res?.data ?? [] as entry, idx (entry.owner.username)}
				<Table.Row
					class={[
						'h-12',
						entry.owner.username === page.data.user?.username ? 'bg-accent/50' : 'hover:bg-muted/50'
					]}
				>
					<Table.Cell align="center">
						<span
							class={[
								'mx-auto flex size-7 items-center justify-center text-sm font-semibold tabular-nums',
								medals[idx] ?? 'text-muted-foreground'
							]}
						>
							{idx + 1}
						</span>
					</Table.Cell>
					<Table.Cell>
						<div class="flex items-center gap-3">
							<UserAvatar username={entry.owner.username} />
							<span class={idx < 3 ? 'font-medium' : undefined}>
								{entry.owner.first_name}
								{entry.owner.last_name}
							</span>
						</div>
					</Table.Cell>
					<Table.Cell align="right" class="pr-5 font-medium">{value(entry)}</Table.Cell>
				</Table.Row>
			{/each}
		</Table.Body>
	</Table.Root>
</Card>
