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
	// Lines that only bring money in, like sponsorships
	const incomeOf = (bl: BudgetLine) => (budgetOf(bl) === 0 ? num(bl.income) : 0);

	// Expense budget and spending of a group of lines
	function totals(lines: BudgetLine[]) {
		const budget = lines.reduce((sum, bl) => sum + budgetOf(bl), 0);
		const used = lines.reduce((sum, bl) => sum + num(bl.amount_uploaded), 0);
		return { budget, used, rest: budget - used };
	}

	function expensesHref(scc: string, line: string) {
		const params = new URLSearchParams({
			cost_centre: costCentre.name,
			secondary_cost_centre: scc,
			budget_line: line
		});
		return `/admin/expenses/?${params}`;
	}

	const restTone = (rest: number) => (rest < 0 ? 'text-danger-text' : 'text-primary-text');

	const spent = $derived(num(costCentre.amount_uploaded));
	const stats = $derived([
		{ label: $_('budget.budget'), value: costCentre.expense },
		{ label: $_('budget.spent'), value: spent },
		{ label: $_('budget.rest'), value: costCentre.expense - spent, rest: true }
	]);
</script>

{#snippet budgetCell(bl: BudgetLine)}
	{#if incomeOf(bl) > 0}
		<span class="text-primary-text">+{formatKronor(incomeOf(bl))}</span>
	{:else}
		{@render amount(budgetOf(bl))}
	{/if}
{/snippet}

{#snippet amount(value: number, colored = false)}
	{#if value === 0}
		<span class="text-muted-foreground">–</span>
	{:else}
		<!-- Colored amounts are what's left: green within budget, red over it -->
		<span class={[colored && restTone(value)]}>{formatKronor(value)}</span>
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
			{:else if incomeOf(bl) > 0}
				<Badge variant="success">{$_('budget.income')}</Badge>
			{/if}
		</span>
		{#if bl.comment}
			<span class="text-xs text-muted-foreground">{bl.comment}</span>
		{/if}
	</div>
{/snippet}

{#snippet lineBar(bl: BudgetLine)}
	{#if num(bl.amount_uploaded) > 0}
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
						class={['text-lg font-bold tabular-nums sm:text-xl', stat.rest && restTone(stat.value)]}
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
		<p class="p-5 text-sm text-danger-text">{$_('budget.load_error')}</p>
	{:else}
		{@const groups = detail.value?.secondary_cost_centres
			?.map((scc) => ({
				scc,
				total: totals(scc.budget_lines ?? []),
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
			{#each groups ?? [] as { scc, total, lines } (scc.id)}
				<li class="flex items-baseline justify-between gap-3 bg-muted px-5 py-2.5 font-bold">
					<span class="min-w-0 wrap-break-word">{scc.name}</span>
					<span class="text-sm tabular-nums">{@render amount(total.rest, true)}</span>
				</li>
				{#each lines as bl (bl.id)}
					{@const budget = budgetOf(bl)}
					{@const used = num(bl.amount_uploaded)}
					<li class="flex flex-col gap-2.5 px-5 py-3 text-sm">
						{@render lineName(scc.name, bl)}
						{@render lineBar(bl)}
						<dl class="grid grid-cols-3 gap-2 text-xs tabular-nums">
							<div class="flex flex-col">
								<dt class="text-muted-foreground">{$_('budget.budget')}</dt>
								<dd class="font-semibold">{@render budgetCell(bl)}</dd>
							</div>
							<div class="flex flex-col">
								<dt class="text-muted-foreground">{$_('budget.spent')}</dt>
								<dd class="font-semibold">{@render amount(used)}</dd>
							</div>
							<div class="flex flex-col items-end">
								<dt class="text-muted-foreground">{$_('budget.rest')}</dt>
								<dd class="font-bold">
									{#if budget > 0}
										{@render amount(budget - used, true)}
									{:else}
										<span class="text-muted-foreground">–</span>
									{/if}
								</dd>
							</div>
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
					{#each groups ?? [] as { scc, total, lines } (scc.id)}
						<Table.Row class="bg-muted font-bold">
							<Table.Cell class="h-11 pl-5">{scc.name}</Table.Cell>
							<Table.Cell align="right">{@render amount(total.budget)}</Table.Cell>
							<Table.Cell align="right">{@render amount(total.used)}</Table.Cell>
							<Table.Cell align="right" class="pr-5">
								{@render amount(total.rest, true)}
							</Table.Cell>
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
								<Table.Cell align="right" class="py-3">{@render budgetCell(bl)}</Table.Cell>
								<Table.Cell align="right" class="py-3">{@render amount(used)}</Table.Cell>
								<Table.Cell align="right" class="py-3 pr-5 font-bold">
									{#if budget > 0}
										{@render amount(budget - used, true)}
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
