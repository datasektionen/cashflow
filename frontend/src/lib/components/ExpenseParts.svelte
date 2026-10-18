<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { onMount } from 'svelte';
	import { AlertTriangle, CircleAlert, Plus, TriangleAlert, X } from '@lucide/svelte';
	import ComboBox from '$lib/components/ComboBox.svelte';
	import AmountInput from '$lib/components/AmountInput.svelte';
	import type { BudgetLine, CostCentre, SecondaryCostCentre } from '$lib/api/types';
	import { budget } from '$lib/stores/budget.svelte';
	import type { PartCreateUpdate } from '$lib/api/types';
	import { ZERO, dineroFromDecimal, dineroFromFloat, sumDinero } from '$lib/money';
	import { SEK, subtract } from 'dinero.js';
	import { BUDGET_USAGE_FIELD, sameBudgetLine, type BudgetLineUsage } from '$lib/budgetUsage';

	import { SvelteSet } from 'svelte/reactivity';
	import { api } from '$lib/api';
	import { logger } from '$lib/logger';
	import { fade } from 'svelte/transition';

	function newPart(): PartCreateUpdate {
		return {
			cost_centre: '',
			secondary_cost_centre: '',
			budget_line: '',
			amount: ZERO
		};
	}

	type Props = {
		parts: PartCreateUpdate[];
		// The budget usage of each part's budget line, for the validation suite
		budgetUsage: (BudgetLineUsage | null)[];
		errors: Record<string, string[]>;
		warnings: Record<string, string[]>;
		showErrors: (field: string) => boolean;
		onValidate: (field: string) => void;
		addPartPrompt?: string;
	};

	let {
		parts = $bindable(),
		budgetUsage = $bindable(),
		errors,
		warnings,
		showErrors,
		onValidate,
		addPartPrompt
	}: Props = $props();

	let costCentres: CostCentre[] = $state([]);
	let secondaryCostCentresByPart: SecondaryCostCentre[][] = $state([]);
	let budgetLinesByPart: BudgetLine[][] = $state([]);
	// The parts as they were when the form was opened. When updating a claim,
	// these are already included in the budget lines' uploaded amounts.
	let initialParts: PartCreateUpdate[] = [];

	onMount(async () => {
		initialParts = parts.map((part) => ({ ...part }));

		loading.add(-1);
		costCentres = await budget.costCentres.list().then((res) => res.filter((cc) => cc.active));
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
		if (costCentre?.id != null) {
			secondaryCostCentresByPart[i] = (
				(await budget.secondaryCostCentres.get(costCentre)) ?? []
			).filter((scc) => scc.cost_centre_id === costCentre.id && scc.active);
		} else {
			secondaryCostCentresByPart[i] = [];
		}

		await loadBudgetLines(i);
	}

	async function loadBudgetLines(i: number) {
		const secondaryCostCentre = secondaryCostCentresByPart[i]?.find(
			(scc) => scc.name === parts[i].secondary_cost_centre
		);
		if (secondaryCostCentre?.id != null) {
			const budgetLines = (await budget.budgetLines.get(secondaryCostCentre)) ?? [];
			budgetLinesByPart[i] = budgetLines.filter((bl) => bl.active);
		} else {
			// Fetch all
			budgetLinesByPart[i] = [];
		}
	}

	function onCostCentreChange(i: number, value: string) {
		loading.add(i);
		parts[i].cost_centre = value;
		parts[i].secondary_cost_centre = '';
		parts[i].budget_line = '';
		budgetUsage[i] = null;
		loadSecondaryCostCentres(i);
		loading.delete(i);
	}

	function onSecondaryCostCentreChange(i: number, value: string) {
		loading.add(i);
		parts[i].secondary_cost_centre = value;
		parts[i].budget_line = '';
		budgetUsage[i] = null;
		loadBudgetLines(i);
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

	function addPart() {
		parts = [...parts, newPart()];
		secondaryCostCentresByPart = [...secondaryCostCentresByPart, []];
		budgetLinesByPart = [...budgetLinesByPart, []];
		budgetUsage = [...budgetUsage, null];
		loadBudgetLines(parts.length - 1);
	}

	function removePart(i: number) {
		parts = parts.filter((_, j) => j !== i);
		secondaryCostCentresByPart = secondaryCostCentresByPart.filter((_, j) => j !== i);
		budgetLinesByPart = budgetLinesByPart.filter((_, j) => j !== i);
		budgetUsage = budgetUsage.filter((_, j) => j !== i);
	}

	// A set of currently loading parts
	let loading: SvelteSet<number> = $state(new SvelteSet<number>());
</script>

{#snippet fieldError(field: string, extra = '')}
	{#if showErrors(field)}
		<span
			class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase {extra}"
		>
			<span>{$_(errors[field]![0])}</span>
			<CircleAlert class="size-4" />
		</span>
	{/if}
{/snippet}

<div class="flex flex-col">
	{#each parts as part, i}
		<div class="flex bg-base-300 p-4 md:justify-between dark:bg-dark-base-300">
			<div
				class="flex w-full flex-wrap justify-between border-b border-base-500 lg:flex-row dark:border-dark-base-200"
			>
				<div class="flex flex-col space-y-1">
					{#if i === 0}<span class="mb-1 text-sm font-medium"
							>{$_('new_expense.form.expense_parts.cost_center_label')}</span
						>{/if}
					<ComboBox
						name="part-{i}-costcenter"
						placeholder={$_('new_expense.form.expense_parts.cost_center_placeholder')}
						items={costCentres.map((cc) => cc.name)}
						bind:value={part.cost_centre}
						onchange={(v) => onCostCentreChange(i, v)}
						onblur={() => onValidate(`part-${i}-costcenter`)}
						loading={loading.has(i) || loading.has(-1)}
					/>
					{@render fieldError(`part-${i}-costcenter`)}
				</div>
				<div class="flex flex-col space-y-1">
					{#if i === 0}<span class="mb-1 text-sm font-medium"
							>{$_('new_expense.form.expense_parts.secondary_cost_center_label')}</span
						>{/if}
					<ComboBox
						name="part-{i}-secondarycostcenter"
						placeholder={$_('new_expense.form.expense_parts.secondary_cost_center_placeholder')}
						items={(secondaryCostCentresByPart[i] ?? []).map((scc) => scc.name)}
						bind:value={part.secondary_cost_centre}
						onchange={(v) => onSecondaryCostCentreChange(i, v)}
						onblur={() => onValidate(`part-${i}-secondarycostcenter`)}
						loading={loading.has(i) || loading.has(-1)}
						locked={part.cost_centre === ''}
					/>
					{@render fieldError(`part-${i}-secondarycostcenter`)}
				</div>
				<div class="flex flex-col space-y-1">
					{#if i === 0}<span class="mb-1 text-sm font-medium"
							>{$_('new_expense.form.expense_parts.budget_line_label')}</span
						>{/if}
					<ComboBox
						name="part-{i}-budgetline"
						placeholder={$_('new_expense.form.expense_parts.budget_line_placeholder')}
						items={(budgetLinesByPart[i] ?? []).map((bl) => bl.name)}
						bind:value={part.budget_line}
						onchange={(v) => onBudgetLineChange(i, v)}
						onblur={() => onValidate(`part-${i}-budgetline`)}
						loading={loading.has(i) || loading.has(-1)}
						locked={part.secondary_cost_centre === ''}
					/>
					{#if budgetUsage[i] && warnings[`part-${i}-budgetline`]?.length}
						<div
							in:fade={{ duration: 150 }}
							class="flex w-0 min-w-full animate-pulse flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-amber-400 uppercase"
						>
							<TriangleAlert class="size-4 shrink-0" />
							<p class="text-xs font-medium">
								{$_(warnings[`part-${i}-budgetline`]![0])}
							</p>
						</div>
					{/if}

					{@render fieldError(`part-${i}-budgetline`)}
				</div>
				<div class="flex flex-col space-y-1">
					{#if i === 0}<span class="mb-1 text-right text-sm font-medium"
							>{$_('new_expense.form.expense_parts.amount_label')}</span
						>{/if}
					<div class="flex bg-base-300 dark:bg-dark-base-300">
						<AmountInput
							name="part-{i}-amount"
							bind:value={
								() => part.amount,
								(v) => {
									part.amount = v ?? ZERO;
									onValidate(BUDGET_USAGE_FIELD);
								}
							}
							suffix="SEK"
						/>
					</div>
					{@render fieldError(`part-${i}-amount`, 'justify-end')}
				</div>
				<button
					type="button"
					onclick={() => removePart(i)}
					class="ml-4 text-base-subtle transition-all hover:scale-125 hover:cursor-pointer dark:text-dark-base-subtle"
				>
					{#if i > 0}
						<X />
					{/if}
				</button>
			</div>
		</div>
	{/each}
	<button
		type="button"
		onclick={addPart}
		class="group mt-2 flex cursor-pointer flex-col items-center justify-center gap-1 border-0 bg-base-300 py-3 dark:bg-dark-base-300"
	>
		<span
			class="flex size-10 items-center rounded-full transition-all group-hover:bg-base-100 dark:group-hover:bg-dark-base-100"
		>
			<Plus class="m-auto" />
		</span>
		<span class="text-center text-xs font-medium text-base-subtle dark:text-dark-base-subtle">
			{addPartPrompt}
		</span>
	</button>
</div>
