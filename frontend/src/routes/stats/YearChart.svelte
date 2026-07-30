<script lang="ts">
	import { scaleBand } from 'd3-scale';
	import { Axis, Bar, Chart, Layer } from 'layerchart';
	import { cubicInOut } from 'svelte/easing';
	import { api } from '$lib/api';
	import { locale } from 'svelte-i18n';
	import { ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { isSmallLayout } from '$lib/stores/state.svelte';

	const currentYear = new Date().getFullYear();
	let { year = currentYear, mode = 'total' }: { year?: number; mode?: 'total' | 'count' } =
		$props();

	let monthFmt = $derived(new Intl.DateTimeFormat($locale ?? 'sv', { month: 'short' }));

	let data = $state<{ month: string; expense_count: number; expense_total: number }[]>([]);

	$effect(() => {
		const y = year;
		const fmt = monthFmt;
		let cancelled = false;
		api.stats.yearly(y).then((value) => {
			if (cancelled) return;
			data = value.months.map((month) => ({
				month: fmt.format(new Date(y, month.month - 1)),
				expense_count: Number(month.expense_count),
				expense_total: Number(month.expense_total)
			}));
		});
		return () => {
			cancelled = true;
		};
	});
</script>

<div class="flex flex-row">
	<div class="flex flex-row">
		<button
			class="size-6 cursor-pointer transition-all hover:scale-115"
			onclick={() => {
				year--;
			}}
		>
			<ChevronLeft class="m-auto size-5" />
		</button>
		<div>
			{year}
		</div>
		<button
			class="size-6 cursor-pointer transition-all hover:scale-115 disabled:cursor-not-allowed disabled:text-base-subtle disabled:opacity-40 disabled:hover:scale-100 dark:disabled:text-dark-base-subtle"
			onclick={() => {
				year++;
			}}
			disabled={year >= currentYear}
		>
			<ChevronRight class="m-auto size-5" />
		</button>
	</div>

	<div
		class="relative ml-auto flex w-24 shrink-0 flex-row overflow-hidden bg-base-300 dark:bg-dark-base-300"
	>
		<div
			class={[
				'absolute inset-y-0 w-12 bg-money-green-500 transition-all',
				mode === 'total' && 'left-0',
				mode === 'count' && 'left-12'
			]}
		></div>

		<button
			onclick={() => (mode = 'total')}
			class={[
				'z-2 w-12 cursor-pointer py-1.5 text-center text-xs font-medium uppercase transition-colors',
				mode === 'total' ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
			]}
			>Summa
		</button>
		<button
			onclick={() => (mode = 'count')}
			class={[
				'z-2 w-12 cursor-pointer py-1.5 text-center text-xs font-medium uppercase transition-colors',
				mode === 'count' ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
			]}
			>Antal
		</button>
	</div>
</div>

{#if data.length}
	<Chart
		{data}
		x="month"
		xScale={scaleBand().padding(0.4)}
		y={mode === 'total' ? 'expense_total' : 'expense_count'}
		yDomain={[0, null]}
		yNice
		height={isSmallLayout.current ? 240 : 400}
		padding={{ left: 24, bottom: 20, top: 8 }}
	>
		<Layer>
			<Axis placement="left" grid rule />
			<Axis placement="bottom" rule />
			{#each data as d, i}
				<Bar
					data={d}
					fill="var(--color-money-green-500)"
					radius={0}
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
{/if}
