<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { TriangleAlert } from '@lucide/svelte';
	import { api } from '#lib/api/index.ts';
	import { latest } from '#lib/latest.svelte.ts';
	import type { BudgetLine, CostCentreSummary, User } from '#lib/api/types.ts';
	import { hasAdminAccess } from '#lib/auth.ts';
	import { Badge, Card, Skeleton, Table } from '#lib/components/ui/index.ts';
	import { formatKronor } from '#lib/money.ts';
	import UsageBar from './UsageBar.svelte';

	let {
		costCentre,
		year,
		blownOnly,
		user
	}: { costCentre: CostCentreSummary; year: number; blownOnly: boolean; user: User | null } =
		$props();

	const detail = latest(() => api.budget.retrieveCostCentre(costCentre.id, year));

	let tableScroll = $state<HTMLElement | null>(null);
	$effect(() => {
		void costCentre.id;
		tableScroll?.scrollTo({ top: 0 });
	});
	const admin = $derived(hasAdminAccess(user));

	const num = (v?: string | number | null) => Number(v ?? 0);
	const budgetOf = (bl: BudgetLine) => Math.abs(num(bl.expense));

	function expensesHref(scc: string, line: string) {
		const params = new URLSearchParams({
			cost_centre: costCentre.name,
			secondary_cost_centre: scc,
			budget_line: line
		});
		return `/admin/expenses/?${params}`;
	}

	const spent = $derived(num(costCentre.amount_uploaded));
	const stats = $derived([
		{ label: $_('budget.budget'), value: costCentre.expense },
		{ label: $_('budget.spent'), value: spent },
		{ label: $_('budget.rest'), value: costCentre.expense - spent }
	]);
</script>

{#snippet amount(value: number, tone?: 'danger')}
	{#if value === 0}
		<span class="text-muted-foreground">–</span>
	{:else}
		<span class={tone === 'danger' ? 'text-danger' : ''}>{formatKronor(value)}</span>
	{/if}
{/snippet}

{#snippet lineName(scc: string, bl: BudgetLine)}
	<div class="flex min-w-0 flex-col gap-0.5">
		<span class="flex min-w-0 items-center gap-2">
			{#if admin}
				<a
					href={expensesHref(scc, bl.name)}
					class="min-w-0 font-medium wrap-break-word underline-offset-4 hover:underline"
				>
					{bl.name}
				</a>
			{:else}
				<span class="min-w-0 font-medium wrap-break-word">{bl.name}</span>
			{/if}
			{#if bl.blown}
				<Badge variant="danger"><TriangleAlert />{$_('budget.exceeded')}</Badge>
			{/if}
		</span>
		{#if bl.comment}
			<span class="text-xs text-muted-foreground">{bl.comment}</span>
		{/if}
	</div>
{/snippet}

{#snippet lineBar(bl: BudgetLine)}
	{#if budgetOf(bl) > 0 || num(bl.amount_uploaded) > 0}
		<UsageBar
			budget={budgetOf(bl)}
			uploaded={num(bl.amount_uploaded)}
			attested={num(bl.amount_attested)}
			paid={num(bl.amount_paid)}
			legend
		/>
	{/if}
{/snippet}

<Card padded={false} class="flex min-w-0 flex-col lg:h-full">
	<div class="flex flex-col gap-4 border-b border-border px-5 py-4">
		<h2 class="text-lg font-bold tracking-tight wrap-break-word">{costCentre.name}</h2>
		<dl class="grid grid-cols-3 gap-4">
			{#each stats as stat (stat.label)}
				<div class="flex flex-col gap-0.5">
					<dt class="text-xs text-muted-foreground">{stat.label}</dt>
					<dd
						class={['text-lg font-bold tabular-nums sm:text-xl', stat.value < 0 && 'text-danger']}
					>
						{formatKronor(stat.value)}
					</dd>
				</div>
			{/each}
		</dl>
		<UsageBar
			budget={costCentre.expense}
			uploaded={spent}
			attested={num(costCentre.amount_attested)}
			paid={num(costCentre.amount_paid)}
			legend
		/>
	</div>

	{#if detail.error}
		<p class="p-5 text-sm text-danger">{$_('budget.load_error')}</p>
	{:else}
		{@const groups = detail.value?.secondary_cost_centres
			?.map((scc) => ({
				scc,
				lines: (scc.budget_lines ?? []).filter((bl) => !blownOnly || bl.blown)
			}))
			.filter((g) => g.lines.length > 0)}
		{@const dimmed = detail.loading && !!detail.value}

		<ul class={['divide-y divide-border transition-opacity sm:hidden', dimmed && 'opacity-60']}>
			{#if !detail.value}
				<li class="bg-muted/60 px-5 py-2"><Skeleton class="h-4 w-24" /></li>
				{#each { length: 4 }, i (i)}
					<li class="flex flex-col gap-2.5 px-5 py-3">
						<Skeleton class="h-5 w-40" />
						<Skeleton class="h-2" />
						<Skeleton class="h-8" />
					</li>
				{/each}
			{/if}
			{#each groups ?? [] as { scc, lines } (scc.id)}
				<li class="bg-muted/60 px-5 py-2 text-xs font-semibold">{scc.name}</li>
				{#each lines as bl (bl.id)}
					{@const budget = budgetOf(bl)}
					{@const used = num(bl.amount_uploaded)}
					<li class="flex flex-col gap-2.5 px-5 py-3 text-sm">
						{@render lineName(scc.name, bl)}
						{@render lineBar(bl)}
						<dl class="grid grid-cols-3 gap-2 text-xs tabular-nums">
							{#each [{ label: $_('budget.budget'), value: budget }, { label: $_('budget.spent'), value: used }, { label: $_('budget.rest'), value: budget > 0 ? budget - used : null }] as cell, i (cell.label)}
								<div class={['flex flex-col', i === 2 && 'items-end']}>
									<dt class="text-muted-foreground">{cell.label}</dt>
									<dd
										class={['font-semibold', cell.value != null && cell.value < 0 && 'text-danger']}
									>
										{cell.value == null ? '–' : formatKronor(cell.value)}
									</dd>
								</div>
							{/each}
						</dl>
					</li>
				{/each}
			{/each}
		</ul>

		<div
			bind:this={tableScroll}
			class={[
				'hidden min-h-0 flex-1 overflow-auto overscroll-contain transition-opacity sm:block',
				dimmed && 'opacity-60'
			]}
		>
			<table class="w-full min-w-[38rem] text-sm tabular-nums">
				<Table.Header class="sticky top-0 z-10 bg-card shadow-[0_1px_0_var(--border)]">
					<Table.Row class="border-0">
						<Table.Head class="pl-5">{$_('budget_line')}</Table.Head>
						<Table.Head align="right" class="w-32">{$_('budget.budget')}</Table.Head>
						<Table.Head align="right" class="w-32">{$_('budget.spent')}</Table.Head>
						<Table.Head align="right" class="w-32 pr-5">{$_('budget.rest')}</Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#if !detail.value}
						<Table.Row class="bg-muted/60">
							<Table.Cell colspan={4} class="h-9 pl-5"><Skeleton class="h-3 w-24" /></Table.Cell>
						</Table.Row>
						{#each { length: 6 }, i (i)}
							<Table.Row class="align-top">
								<Table.Cell class="py-3 pl-5">
									<div class="flex flex-col gap-2">
										<Skeleton class="h-5 w-40" />
										<Skeleton class="h-2" />
										<Skeleton class="h-3 w-48" />
									</div>
								</Table.Cell>
								{#each { length: 3 }, j (j)}
									<Table.Cell class="py-3 last:pr-5"
										><Skeleton class="ml-auto h-5 w-16" /></Table.Cell
									>
								{/each}
							</Table.Row>
						{/each}
					{/if}
					{#each groups ?? [] as { scc, lines } (scc.id)}
						<Table.Row class="bg-muted/60">
							<Table.Cell colspan={4} class="h-9 pl-5 text-xs font-semibold">{scc.name}</Table.Cell>
						</Table.Row>
						{#each lines as bl (bl.id)}
							{@const budget = budgetOf(bl)}
							{@const used = num(bl.amount_uploaded)}
							<Table.Row class="align-top hover:bg-muted/40">
								<Table.Cell class="py-3 pl-5">
									<div class="flex min-w-0 flex-col gap-2">
										{@render lineName(scc.name, bl)}
										{@render lineBar(bl)}
									</div>
								</Table.Cell>
								<Table.Cell align="right" class="py-3">{@render amount(budget)}</Table.Cell>
								<Table.Cell align="right" class="py-3">{@render amount(used)}</Table.Cell>
								<Table.Cell align="right" class="py-3 pr-5 font-semibold">
									{#if budget > 0}
										{@render amount(budget - used, budget - used < 0 ? 'danger' : undefined)}
									{/if}
								</Table.Cell>
							</Table.Row>
						{/each}
					{/each}
				</Table.Body>
			</table>
		</div>
	{/if}
</Card>
