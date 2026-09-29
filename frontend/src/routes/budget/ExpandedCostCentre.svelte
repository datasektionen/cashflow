<script lang="ts">
	import { api } from '$lib/api';
	import type { BudgetLine, CostCentre, SecondaryCostCentre, User } from '$lib/api/types';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { formatAmount } from '$lib/money';
	import { _ } from 'svelte-i18n';
	import { Receipt, SquareArrowOutUpRight, TriangleAlert } from '@lucide/svelte';
	import { hasAdminAccess } from '$lib/auth';

	let {
		costCentre,
		filterBlown,
		user
	}: { costCentre: CostCentre; filterBlown: boolean; user: User | null } = $props();

	let detailedRes = $derived.by(async () => {
		const detail = await api.budget.retrieveCostCentre(costCentre.id!);
		return detail;
	});

	// Context menu
	let ctx: {
		budgetLine: BudgetLine;
		secondaryCostCentre: SecondaryCostCentre;
		x: number;
		y: number;
	} | null = $state(null);
	// Dismiss context table
	$effect(() => {
		if (!ctx) return;
		const close = () => (ctx = null);
		const onKeyDown = (e: KeyboardEvent) => {
			if (e.key === 'Escape') close();
		};
		window.addEventListener('click', close);
		window.addEventListener('scroll', close, true);
		window.addEventListener('keydown', onKeyDown);
		return () => {
			window.removeEventListener('click', close);
			window.removeEventListener('scroll', close, true);
			window.removeEventListener('keydown', onKeyDown);
		};
	});

	const itemClass =
		'flex w-full cursor-pointer flex-row items-center gap-x-2 px-3 py-2 text-left transition-colors hover:bg-base-300 focus-visible:bg-base-300 focus-visible:outline-none dark:hover:bg-dark-base-300 dark:focus-visible:bg-dark-base-300';
</script>

<!-- Context menu -->
{#if ctx != null}
	{@const url = encodeURIComponent}
	<div
		role="menu"
		class={[
			'fixed z-10 flex w-52 flex-col border border-base-500 bg-base-100 py-1 shadow-lg',
			'text-sm text-base-text dark:border-dark-base-300 dark:bg-dark-base-200 dark:text-dark-base-text'
		]}
		style="left: {ctx.x}px; top: {ctx.y}px"
	>
		<a
			href="/admin/expenses/?cost_centre={url(costCentre.name)}&secondary_cost_centre={ctx
				.secondaryCostCentre.name}&budget_line={url(ctx.budgetLine.name)}"
			role="menuitem"
			class={itemClass}
			target="_blank"
			rel="noopener noreferrer"
		>
			<Receipt class="size-4" />
			{$_('Visa utlägg')}
			<SquareArrowOutUpRight class="ml-auto size-3 text-base-subtle dark:text-dark-base-subtle" />
		</a>
		<a
			href="/admin/invoices/?cost_centre={url(costCentre.name)}&secondary_cost_centre={url(
				ctx.secondaryCostCentre.name
			)}&budget_line={url(ctx.budgetLine.name)}"
			role="menuitem"
			class={itemClass}
			target="_blank"
			rel="noopener noreferrer"
		>
			<Receipt class="size-4" />
			{$_('Visa fakturor')}
			<SquareArrowOutUpRight class="ml-auto size-3 text-base-subtle dark:text-dark-base-subtle" />
		</a>
	</div>
{/if}

{#await detailedRes}
	<CashSpinner class="mx-auto text-money-green-500 opacity-50" />
{:then detail}
	<div class="w-full">
		<div
			class="hidden items-center gap-4 px-4 pb-2 text-xs font-medium tracking-wide text-base-subtle uppercase md:flex dark:text-dark-base-subtle"
		>
			<div class="w-64 shrink-0"></div>
			<div class="flex-1"></div>
			<div class="w-32 shrink-0 text-right">{$_('budget.total')}</div>
			<div class="w-32 shrink-0 text-right">{$_('budget.rest')}</div>
		</div>

		{#each detail.secondary_cost_centres ?? [] as scc}
			{@const budgetLines = scc.budget_lines?.filter((bl) => (filterBlown ? bl.blown : true)) ?? []}
			{#if budgetLines.length > 0}
				<div
					class="px-4 pt-8 pb-2 text-sm font-semibold tracking-wide text-base-subtle uppercase dark:text-dark-base-subtle"
				>
					{scc.name}
				</div>

				{#each budgetLines as bl, i}
					<div
						class="flex flex-col gap-4 border-b border-base-500 px-4 py-4 hover:bg-base-200 md:flex-row md:items-center dark:border-dark-base-200 dark:hover:bg-dark-base-200"
						role="row"
						tabindex={i}
						oncontextmenu={(e) => {
							if (hasAdminAccess(user)) {
								e.preventDefault();
								ctx = { budgetLine: bl, secondaryCostCentre: scc, x: e.clientX, y: e.clientY };
							}
						}}
					>
						{#if hasAdminAccess(user)}
							{@const url = encodeURIComponent}
							<a
								class="w-64 shrink-0 font-medium hover:underline"
								href={`/admin/expenses/?cost_centre=${url(costCentre.name)}&secondary_cost_centre=${url(scc.name)}&budget_line=${url(bl.name)}`}
								>{bl.name}</a
							>
						{:else}
							<div class="w-64 shrink-0 font-medium">{bl.name}</div>
						{/if}

						<div class="flex-1">
							{#if bl.expense}
								{@const num = (v?: string) => parseFloat(v ? v : '0')}
								{@const pct = (v?: string) =>
									Math.max(0, Math.min(100, (num(v) / Math.abs(bl.expense!)) * 100))}
								{@const blown = num(bl.amount_paid) > Math.abs(bl.expense!)}
								{@const alert = num(bl.amount_uploaded) > Math.abs(bl.expense!)}
								{@const barColor = blown
									? 'bg-red-400'
									: alert
										? 'bg-money-green-500 md:bg-amber-400'
										: 'bg-money-green-500'}

								<div class="relative h-4 w-full bg-base-600 dark:bg-dark-base-50">
									<span
										class={['absolute top-0 left-0 hidden h-full opacity-40 md:flex', barColor]}
										style="width: {pct(bl.amount_uploaded)}%"
									></span>
									<span
										class={['absolute top-0 left-0 hidden h-full opacity-70 md:flex', barColor]}
										style="width: {pct(bl.amount_attested)}%"
									></span>
									<span
										class={['absolute top-0 left-0 h-full', barColor]}
										style="width: {pct(bl.amount_paid)}%"
									></span>
								</div>
								<div
									class="mt-1 flex flex-wrap gap-3 text-xs text-base-subtle dark:text-dark-base-subtle"
								>
									<span
										class={[
											'hidden items-center gap-1 md:flex',
											blown && 'font-bold text-base-text dark:text-dark-base-text'
										]}
									>
										<span class={['inline-block size-2', barColor]}></span>
										{$_('budget.paid')}
										{formatAmount(bl.amount_paid ?? '0')}
									</span>
									<span class="hidden items-center gap-1 md:flex">
										<span class={['inline-block size-2 opacity-70', barColor]}></span>
										{$_('budget.attested')}
										{formatAmount(bl.amount_attested ?? '0')}
									</span>
									<span
										class={[
											'hidden items-center gap-1 md:flex',
											alert && 'font-bold text-base-text dark:text-dark-base-text'
										]}
									>
										<span class={['inline-block size-2 opacity-40', barColor]}></span>
										{$_('budget.uploaded')}
										{formatAmount(bl.amount_uploaded ?? '0')}
									</span>
									<span
										class="ml-auto hidden text-xs text-base-subtle md:flex dark:text-dark-base-subtle"
									>
										(Diff. {formatAmount(-bl.expense - num(bl.amount_uploaded))})
									</span>
								</div>
							{/if}
						</div>

						<div
							class="w-full shrink-0 text-left whitespace-nowrap tabular-nums md:w-32 md:text-right"
						>
							{#if bl.expense}
								{@const num = (v?: string) => parseFloat(v ? v : '0')}
								{@const blown =
									num(bl.amount_attested) > Math.abs(bl.expense!) ||
									num(bl.amount_paid) > Math.abs(bl.expense!)}
								{@const alert = num(bl.amount_uploaded) > Math.abs(bl.expense!)}
								{@const textColor = blown
									? 'text-red-400'
									: alert
										? 'text-base-text dark:text-dark-base-text md:text-amber-400'
										: 'text-base-text dark:text-dark-base-text'}
								<span class={['font-medium md:hidden', textColor]}>
									{formatAmount(bl.amount_paid ?? '0')}
								</span>
								<span class="text-base-subtle md:hidden dark:text-dark-base-subtle">/</span>
								{formatAmount(Math.abs(bl.expense))}
							{/if}
						</div>

						<div
							class="w-full shrink-0 text-left whitespace-nowrap tabular-nums md:w-32 md:text-right"
						>
							{#if bl.expense}
								{@const rest = Math.abs(bl.expense) - parseFloat(bl.amount_paid ?? '0')}
								<span class={rest < 0 ? 'text-red-400' : undefined}>
									{formatAmount(rest)}
								</span>
							{/if}
						</div>
					</div>
				{/each}
			{/if}
		{/each}
	</div>
{:catch e}
	<div class="flex items-center gap-2 px-4 py-4 text-sm text-red-400">
		<TriangleAlert class="size-4 shrink-0" />
		{$_('budget.load_error')}
	</div>
{/await}
