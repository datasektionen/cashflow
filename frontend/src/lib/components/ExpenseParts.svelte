<script lang="ts" module>
	import type { PartCreateUpdate } from '#lib/api/types.ts';
	import { ZERO } from '#lib/money.ts';

	export const newPart = (): PartCreateUpdate => ({
		cost_centre: '',
		secondary_cost_centre: '',
		budget_line: '',
		amount: ZERO
	});

	/** The form parts for editing a claim's saved parts. */
	export const editableParts = (parts: PartCreateUpdate[]): PartCreateUpdate[] =>
		parts.length > 0
			? parts.map(({ cost_centre, secondary_cost_centre, budget_line, amount }) => ({
					cost_centre,
					secondary_cost_centre,
					budget_line,
					amount
				}))
			: [newPart()];
</script>

<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { onMount, tick } from 'svelte';
	import { CircleAlert, Plus, TriangleAlert, X } from '@lucide/svelte';
	import AmountInput from '#lib/components/AmountInput.svelte';
	import type { BudgetLine, CostCentre, SecondaryCostCentre } from '#lib/api/types.ts';
	import { budget } from '#lib/stores/budget.ts';
	import { dineroFromDecimal, dineroFromFloat, formatDineroAmount, sumDinero } from '#lib/money.ts';
	import { SEK, isNegative, multiply, subtract } from 'dinero.js';
	import {
		BUDGET_USAGE_FIELD,
		budgetLineRemaining,
		sameBudgetLine,
		type BudgetLineUsage
	} from '#lib/budgetUsage.ts';
	import { SvelteSet } from 'svelte/reactivity';
	import { api } from '#lib/api/index.ts';
	import { logger } from '#lib/logger.ts';
	import { fade } from 'svelte/transition';
	import { Button, Combobox } from '#lib/components/ui/index.ts';

	type Props = {
		parts: PartCreateUpdate[];
		// The budget usage of each part's budget line, for the validation suite
		budgetUsage: (BudgetLineUsage | null)[];
		errorFor: (field: string) => string | null;
		onValidate: (field: string) => void;
		addPartPrompt?: string;
	};

	let {
		parts = $bindable(),
		budgetUsage = $bindable(),
		errorFor,
		onValidate,
		addPartPrompt
	}: Props = $props();

	let costCentres: CostCentre[] = $state([]);
	let secondaryCostCentresByPart: SecondaryCostCentre[][] = $state([]);
	let budgetLinesByPart: BudgetLine[][] = $state([]);
	// The parts as they were when the form was opened. When updating a claim,
	// these are already included in the budget lines' uploaded amounts.
	let initialParts: PartCreateUpdate[] = [];
	// Parts whose options are loading; -1 while the cost centres load
	const loading = new SvelteSet<number>();
	const isLoading = (i: number) => loading.has(i) || loading.has(-1);

	onMount(async () => {
		initialParts = parts.map((part) => ({ ...part }));

		budget.preload();
		loading.add(-1);
		costCentres = await budget.costCentres().then((res) => res.filter((cc) => cc.active));
		loading.delete(-1);

		secondaryCostCentresByPart = parts.map(() => []);
		budgetLinesByPart = parts.map(() => []);
		budgetUsage = parts.map(() => null);
		await Promise.all(parts.map((_, i) => loadSecondaryCostCentres(i)));
		await Promise.all(
			parts.map((part, i) => part.budget_line && onBudgetLineChange(i, part.budget_line))
		);
	});

	async function loadSecondaryCostCentres(i: number) {
		const costCentre = costCentres.find((cc) => cc.name === parts[i].cost_centre);
		secondaryCostCentresByPart[i] = costCentre
			? (await budget.secondaryCostCentres(costCentre)).filter((scc) => scc.active)
			: [];

		await loadBudgetLines(i);
	}

	async function loadBudgetLines(i: number) {
		const secondaryCostCentre = secondaryCostCentresByPart[i]?.find(
			(scc) => scc.name === parts[i].secondary_cost_centre
		);
		budgetLinesByPart[i] = secondaryCostCentre
			? (await budget.budgetLines(secondaryCostCentre)).filter((bl) => bl.active)
			: [];
	}

	async function onCostCentreChange(i: number, value: string) {
		parts[i].cost_centre = value;
		parts[i].secondary_cost_centre = '';
		parts[i].budget_line = '';
		budgetUsage[i] = null;
		loading.add(i);
		await loadSecondaryCostCentres(i);
		loading.delete(i);
	}

	async function onSecondaryCostCentreChange(i: number, value: string) {
		parts[i].secondary_cost_centre = value;
		parts[i].budget_line = '';
		budgetUsage[i] = null;
		loading.add(i);
		await loadBudgetLines(i);
		loading.delete(i);
	}

	async function onBudgetLineChange(i: number, value: string) {
		// Fetch the budget line's uploaded amount to check if it is exceeded
		budgetUsage[i] = null;

		const id = budgetLinesByPart[i].find((bl) => bl.name === value)?.id;
		if (id == null) {
			logger.error(`Budget line ${value} not found for part ${i}`);
			return;
		}

		const res = await api.budget.getBudgetLine(id);
		logger.debug(res, `Got budget line ${value} for part ${i}`);

		// Ignore the response if another budget line was selected meanwhile,
		// and lines without an expense budget, which can't be exceeded
		if (parts[i]?.budget_line !== value || !res.expense || res.amount_uploaded == null) {
			return;
		}

		const savedOnLine = sumDinero(
			initialParts.filter((p) => sameBudgetLine(p, parts[i])).map((p) => p.amount)
		);
		budgetUsage[i] = {
			// GOrdian stores expense budgets as negative numbers
			budget: dineroFromFloat(Math.abs(res.expense), SEK),
			uploaded: subtract(dineroFromDecimal(res.amount_uploaded, SEK), savedOnLine)
		};
		onValidate(BUDGET_USAGE_FIELD);
	}

	const focusPart = (i: number) => document.getElementById(`part-${i}-costcenter`)?.focus();

	async function addPart() {
		parts = [...parts, newPart()];
		secondaryCostCentresByPart = [...secondaryCostCentresByPart, []];
		budgetLinesByPart = [...budgetLinesByPart, []];
		budgetUsage = [...budgetUsage, null];
		await tick();
		focusPart(parts.length - 1);
	}

	async function removePart(i: number) {
		parts = parts.filter((_, j) => j !== i);
		secondaryCostCentresByPart = secondaryCostCentresByPart.filter((_, j) => j !== i);
		budgetLinesByPart = budgetLinesByPart.filter((_, j) => j !== i);
		budgetUsage = budgetUsage.filter((_, j) => j !== i);
		await tick();
		focusPart(Math.min(i, parts.length - 1));
	}
</script>

{#snippet fieldError(field: string, extra = '')}
	{@const message = errorFor(field)}
	{#if message}
		<span class="flex items-center gap-1 text-xs font-medium text-danger {extra}">
			<CircleAlert class="size-3.5 shrink-0" />
			{message}
		</span>
	{/if}
{/snippet}

{#snippet remove(i: number, extra = '')}
	<Button
		variant="ghost"
		size="icon"
		aria-label={$_('remove')}
		onclick={() => removePart(i)}
		class={['shrink-0 text-muted-foreground', extra]}
	>
		<X />
	</Button>
{/snippet}

{#snippet label(i: number, field: string, text: string, extra = '')}
	<label for="part-{i}-{field}" class={['text-sm font-medium', i > 0 && '@3xl:sr-only', extra]}>
		{text}
	</label>
{/snippet}

{#snippet budgetField(
	i: number,
	key: 'cost_centre' | 'secondary_cost_centre' | 'budget_line',
	field: string,
	text: string,
	items: string[],
	onchange: (i: number, value: string) => void,
	locked = false
)}
	<div class="flex min-w-0 flex-col gap-1.5">
		{@render label(i, field, $_(`new_expense.form.expense_parts.${text}_label`))}
		<Combobox
			name="part-{i}-{field}"
			id="part-{i}-{field}"
			placeholder={$_(`new_expense.form.expense_parts.${text}_placeholder`)}
			{items}
			bind:value={parts[i][key]}
			onchange={(v) => onchange(i, v)}
			onblur={() => onValidate(`part-${i}-${field}`)}
			loading={isLoading(i)}
			{locked}
		/>
		{#if key === 'budget_line' && budgetUsage[i]}
			{@const remaining = budgetLineRemaining(parts, budgetUsage, i)!}
			{#if isNegative(remaining)}
				<p
					in:fade={{ duration: 150 }}
					class="flex items-center gap-1 text-xs font-medium text-warning-soft-foreground"
				>
					<TriangleAlert class="size-3.5 shrink-0" />
					{$_('budget_line_exceeded_by', {
						values: { amount: formatDineroAmount(multiply(remaining, -1)) }
					})}
				</p>
			{:else}
				<p in:fade={{ duration: 150 }} class="text-xs text-muted-foreground tabular-nums">
					{$_('budget_line_left', { values: { amount: formatDineroAmount(remaining) } })}
				</p>
			{/if}
		{/if}
		{@render fieldError(`part-${i}-${field}`)}
	</div>
{/snippet}

<div class="@container flex flex-col gap-4">
	{#each parts as part, i}
		<div
			class={[
				'grid gap-3 @lg:grid-cols-2 @3xl:items-start',
				parts.length > 1
					? '@3xl:grid-cols-[repeat(3,minmax(0,1fr))_10rem_2.25rem]'
					: '@3xl:grid-cols-[repeat(3,minmax(0,1fr))_10rem]',
				i > 0 && 'border-t border-border pt-4 @3xl:border-0 @3xl:pt-0'
			]}
		>
			{@render budgetField(
				i,
				'cost_centre',
				'costcenter',
				'cost_center',
				costCentres.map((cc) => cc.name),
				onCostCentreChange
			)}
			{@render budgetField(
				i,
				'secondary_cost_centre',
				'secondarycostcenter',
				'secondary_cost_center',
				(secondaryCostCentresByPart[i] ?? []).map((scc) => scc.name),
				onSecondaryCostCentreChange,
				part.cost_centre === ''
			)}
			{@render budgetField(
				i,
				'budget_line',
				'budgetline',
				'budget_line',
				(budgetLinesByPart[i] ?? []).map((bl) => bl.name),
				onBudgetLineChange,
				part.secondary_cost_centre === ''
			)}
			<div class="flex min-w-0 flex-col gap-1.5">
				{@render label(
					i,
					'amount',
					$_('new_expense.form.expense_parts.amount_label'),
					'@3xl:text-right'
				)}
				<div class="flex gap-2">
					<AmountInput
						name="part-{i}-amount"
						id="part-{i}-amount"
						bind:value={
							() => part.amount,
							(v) => {
								part.amount = v ?? ZERO;
								onValidate(BUDGET_USAGE_FIELD);
							}
						}
						suffix="SEK"
					/>
					{#if parts.length > 1}{@render remove(i, '@3xl:hidden')}{/if}
				</div>
				{@render fieldError(`part-${i}-amount`, '@3xl:justify-end')}
			</div>
			{#if parts.length > 1}
				<div class={['hidden justify-end @3xl:flex', i === 0 && '@3xl:pt-6.5']}>
					{@render remove(i)}
				</div>
			{/if}
		</div>
	{/each}
	<Button
		variant="secondary"
		onclick={addPart}
		class={['border-dashed text-muted-foreground', parts.length > 1 && '@3xl:mr-12']}
	>
		<Plus />
		{addPartPrompt}
	</Button>
</div>
