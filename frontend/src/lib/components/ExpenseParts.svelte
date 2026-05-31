<script lang="ts" module>
	export type Part = {
		amountRaw: number | null;
		// We do some pretty formatting for the monetary amount
		// hence the split between the actual (raw) value and the display value
		amountDisplay: string;
		costcenter: string;
		secondarycostcenter: string;
		budgetline: string;
	};

	export function newPart(): Part {
		return {
			amountRaw: null,
			amountDisplay: '',
			costcenter: '',
			secondarycostcenter: '',
			budgetline: ''
		};
	}
</script>

<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { CircleAlert, Plus, X } from '@lucide/svelte';
	import ComboBox from '$lib/components/ComboBox.svelte';

	type Props = {
		parts: Part[];
		costCenters: string[];
		budgetLines: string[];
		errors: Record<string, string[]>;
		showErrors: (field: string) => boolean;
		onValidate: (field: string) => void;
		addPartPrompt?: string;
	};

	let {
		parts = $bindable(),
		costCenters,
		budgetLines,
		errors,
		showErrors,
		onValidate,
		addPartPrompt
	}: Props = $props();

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});

	function onAmountFocus(i: number) {
		parts[i].amountDisplay = parts[i].amountRaw?.toString() ?? '';
	}

	function onAmountBlur(i: number, value: string) {
		const num = parseFloat(value.replace(/\s/g, '').replace(',', '.'));
		if (!isNaN(num) && num >= 0) {
			parts[i].amountRaw = num;
			parts[i].amountDisplay = fmt.format(num);
		} else {
			parts[i].amountRaw = null;
			parts[i].amountDisplay = '';
		}
	}
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
						items={costCenters}
						bind:value={part.costcenter}
						onblur={() => onValidate(`part-${i}-costcenter`)}
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
						items={costCenters}
						bind:value={part.secondarycostcenter}
						onblur={() => onValidate(`part-${i}-secondarycostcenter`)}
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
						items={budgetLines}
						bind:value={part.budgetline}
						onblur={() => onValidate(`part-${i}-budgetline`)}
					/>
					{@render fieldError(`part-${i}-budgetline`)}
				</div>
				<div class="flex flex-col space-y-1">
					{#if i === 0}<span class="mb-1 text-right text-sm font-medium"
							>{$_('new_expense.form.expense_parts.amount_label')}</span
						>{/if}
					<div class="relative flex items-center">
						<input type="hidden" name="part-{i}-amount" value={part.amountRaw ?? ''} />
						<input
							type="text"
							id="part-{i}-amount"
							bind:value={part.amountDisplay}
							onfocus={() => onAmountFocus(i)}
							onblur={(e) => onAmountBlur(i, (e.currentTarget as HTMLInputElement).value)}
							placeholder="0,00"
							class="border-0 bg-base-300 pr-12 text-right placeholder:text-base-subtle dark:bg-dark-base-300 dark:placeholder:text-dark-base-subtle"
						/>
						<span
							class="pointer-events-none absolute right-3 text-sm text-base-subtle dark:text-dark-base-subtle"
							>SEK</span
						>
					</div>
					{@render fieldError(`part-${i}-amount`, 'justify-end')}
				</div>
				<button
					type="button"
					onclick={() => (parts = parts.filter((_, j) => j !== i))}
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
		onclick={() => (parts = [...parts, newPart()])}
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
