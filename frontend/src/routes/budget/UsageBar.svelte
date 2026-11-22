<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { cn } from 'tailwind-variants';
	import { formatKronor } from '#lib/money.ts';

	type Props = {
		budget: number;
		uploaded: number;
		attested?: number;
		paid?: number;
		legend?: boolean;
		thin?: boolean;
		class?: string;
	};

	let {
		budget,
		uploaded,
		attested = 0,
		paid = 0,
		legend = false,
		thin = false,
		class: className
	}: Props = $props();

	// Over budget, the bar extends past the budget and the excess turns red
	const over = $derived(budget > 0 && uploaded > budget ? uploaded - budget : 0);
	const scale = $derived(Math.max(budget, uploaded));
	const pct = (v: number) => (scale > 0 ? Math.min(100, (v / scale) * 100) : 0);
	const limit = $derived(budget > 0 ? budget : scale);

	const stages = $derived([
		{
			label: $_('budget.uploaded'),
			value: uploaded,
			within: 'bg-primary/25',
			beyond: 'bg-danger/30'
		},
		{
			label: $_('budget.attested'),
			value: attested,
			within: 'bg-primary/55',
			beyond: 'bg-danger/60'
		},
		{ label: $_('budget.paid'), value: paid, within: 'bg-primary', beyond: 'bg-danger' }
	]);
</script>

<div class={cn('flex flex-col gap-1', className)}>
	<div aria-hidden="true" class={['relative overflow-hidden bg-muted', thin ? 'h-1' : 'h-2']}>
		{#each stages as stage (stage.label)}
			<div
				class={['absolute inset-y-0 left-0', stage.within]}
				style="width: {pct(Math.min(stage.value, limit))}%"
			></div>
			{#if over && stage.value > budget}
				<div
					class={['absolute inset-y-0', stage.beyond]}
					style="left: {pct(budget)}%; width: {pct(stage.value) - pct(budget)}%"
				></div>
			{/if}
		{/each}
		{#if over}
			<div class="absolute inset-y-0 w-0.5 bg-card" style="left: {pct(budget)}%"></div>
		{/if}
	</div>
	{#if legend && uploaded > 0}
		<div class="flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-muted-foreground tabular-nums">
			{#each [...stages].reverse() as stage (stage.label)}
				<span class="flex items-center gap-1">
					<span class={['size-1.5', stage.within]}></span>
					{stage.label}
					{formatKronor(stage.value)}
				</span>
			{/each}
		</div>
	{/if}
</div>
