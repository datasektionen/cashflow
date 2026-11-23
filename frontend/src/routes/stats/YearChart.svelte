<script lang="ts">
	import { scaleBand } from 'd3-scale';
	import { Axis, Bar, Chart, Layer } from 'layerchart';
	import { cubicInOut } from 'svelte/easing';
	import { api } from '#lib/api/index.ts';
	import { latest } from '#lib/latest.svelte.ts';
	import { _, locale } from 'svelte-i18n';
	import { ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { isSmallLayout } from '#lib/stores/state.svelte.ts';
	import { Button, SegmentedControl, Skeleton } from '#lib/components/ui/index.ts';
	import { toDecimal } from 'dinero.js';

	// Static bar heights (%) for the loading placeholder, one per month
	const skeletonBars = [45, 70, 30, 85, 55, 65, 40, 90, 50, 75, 35, 60];

	const currentYear = new Date().getFullYear();
	let year = $state(currentYear);
	let mode = $state<'total' | 'count'>('total');

	const yearly = latest(() => api.stats.yearly(year));
	const data = $derived.by(() => {
		const fmt = new Intl.DateTimeFormat($locale ?? 'sv', { month: 'short' });
		return (yearly.value?.months ?? []).map((month) => ({
			month: fmt.format(new Date(month.year, month.month - 1)),
			expense_count: Number(month.expense_count),
			expense_total: Number(toDecimal(month.expense_total))
		}));
	});
</script>

<div class="mb-4 flex flex-wrap items-center justify-between gap-3">
	<div class="flex items-center gap-1">
		<Button variant="ghost" size="icon-sm" aria-label={String(year - 1)} onclick={() => year--}>
			<ChevronLeft />
		</Button>
		<span class="w-12 text-center text-sm font-semibold tabular-nums">{year}</span>
		<Button
			variant="ghost"
			size="icon-sm"
			aria-label={String(year + 1)}
			onclick={() => year++}
			disabled={year >= currentYear}
		>
			<ChevronRight />
		</Button>
	</div>

	<SegmentedControl
		size="sm"
		bind:value={mode}
		items={[
			{ value: 'total', label: $_('leaderboard.sum') },
			{ value: 'count', label: $_('leaderboard.count') }
		]}
	/>
</div>

{#if yearly.error}
	<p class="text-sm text-danger-text">{$_('claims.error')}</p>
{:else if data.length}
	<Chart
		{data}
		x="month"
		xScale={scaleBand().padding(0.4)}
		y={mode === 'total' ? 'expense_total' : 'expense_count'}
		yDomain={[0, null]}
		yNice
		height={isSmallLayout.current ? 240 : 400}
		padding={{ left: 40, bottom: 20, top: 8 }}
	>
		<Layer>
			<Axis
				placement="left"
				grid
				tickMarks={false}
				stroke="var(--color-border)"
				fill="var(--color-muted-foreground)"
				classes={{ tickLabel: 'text-xs stroke-card' }}
			/>
			<Axis
				placement="bottom"
				rule
				tickMarks={false}
				stroke="var(--color-border)"
				fill="var(--color-muted-foreground)"
				classes={{ tickLabel: 'text-xs stroke-card' }}
			/>
			{#each data as d, i}
				<Bar
					data={d}
					fill="var(--color-primary)"
					radius={4}
					rounded="top"
					strokeWidth={0}
					motion={{
						type: 'tween',
						duration: 500,
						easing: cubicInOut,
						delay: i * 30
					}}
				/>
			{/each}
		</Layer>
	</Chart>
{:else}
	<div class="flex items-end pt-2 pb-5 pl-10" style="height: {isSmallLayout.current ? 240 : 400}px">
		{#each skeletonBars as h (h)}
			<div class="flex flex-1 justify-center" style="height: {h}%">
				<Skeleton class="h-full w-[60%]" />
			</div>
		{/each}
	</div>
{/if}
