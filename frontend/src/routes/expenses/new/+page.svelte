<script lang="ts">
	import FileInput from './FileInput.svelte';
	import { _, locale } from 'svelte-i18n';
	import {
		BanknoteArrowUp,
		Calendar as CalendarIcon,
		ChevronLeft,
		ChevronRight,
		CircleAlert,
		CircleQuestionMark,
		Plus,
		X
	} from '@lucide/svelte';
	import ComboBox from '$lib/components/ComboBox.svelte';
	import { DatePicker } from 'bits-ui';
	import { type DateValue, getLocalTimeZone, today } from '@internationalized/date';
	import CashSpinner from '$lib/CashSpinner.svelte';
	import validation from './validation.ts';

	const costCenters = [
		'Sektionslokalsgruppen',
		'Mottagningen',
		'D-rektoratet',
		'Studienämnden',
		'Näringslivsnämnden',
		'Internationella nämnden',
		'Idrottsnämnden',
		'Jämlikhetsnämnden',
		'DKM',
		'METAspexet',
		'Fanborgen',
		'Sånggruppen',
		'METAdorerna',
		'Valberedningen',
		'Revisorerna'
	];

	const budgetLines = ['Lokalskostnader', 'Mat och dryck', 'Transport', 'Trycksaker', 'Övrigt'];

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});

	type Part = {
		raw: number | null;
		display: string;
		costcenter: string;
		secondarycostcenter: string;
		budgetline: string;
	};
	let submitting: Boolean = $state(false);
	let description = $state('');
	let receiptFiles: File[] = $state([]);
	let parts: Part[] = $state([
		{ raw: null, display: '', costcenter: '', secondarycostcenter: '', budgetline: '' }
	]);
	let expenseDate: DateValue | undefined = $state();

	function newPart(): Part {
		return { raw: null, display: '', costcenter: '', secondarycostcenter: '', budgetline: '' };
	}

	function onAmountFocus(i: number) {
		parts[i].display = parts[i].raw?.toString() ?? '';
	}

	function onAmountBlur(i: number, value: string) {
		const num = parseFloat(value.replace(/\s/g, '').replace(',', '.'));
		if (!isNaN(num) && num >= 0) {
			parts[i].raw = num;
			parts[i].display = fmt.format(num);
		} else {
			parts[i].raw = null;
			parts[i].display = '';
		}
	}

	function buildValidationData() {
		return {
			description,
			'expense-date': expenseDate?.toString(),
			files: receiptFiles,
			parts: parts.map((p) => ({
				costcenter: p.costcenter,
				secondarycostcenter: p.secondarycostcenter,
				budgetline: p.budgetline,
				amount: p.raw
			}))
		};
	}

	function handleSubmit(e: SubmitEvent) {
		console.log('TEST');
		submitting = true;
		validationResult = validation.run(buildValidationData());
		if (!validationResult.isValid()) {
			e.preventDefault();
			submitting = false;
		}
	}

	let validationResult = $state(validation.get());
	let errors = $derived(validationResult.getErrors());

	function onBlur(e: FocusEvent & { currentTarget: HTMLInputElement }) {
		console.log('blur');
		validationResult = validation.run(buildValidationData(), e.currentTarget.name);
		console.log(validationResult.getErrors().description);
	}

	function onDateBlur(e: FocusEvent) {
		const wrapper = e.currentTarget as HTMLElement;
		if (e.relatedTarget && wrapper.contains(e.relatedTarget as Node)) return;
		validationResult = validation.run(buildValidationData(), 'expense-date');
	}

	function showErrors(field: string) {
		return validationResult.isTested(field) && (errors[field]?.length ?? 0) > 0;
	}
</script>

<form
	method="POST"
	enctype="multipart/form-data"
	onsubmit={handleSubmit}
	class="flex flex-col space-y-4"
>
	<div class="flex flex-col justify-between space-y-6 lg:max-h-128 lg:flex-row lg:space-x-6">
		<fieldset class="flex flex-col space-y-6 border-0 p-0">
			<!-- Description field -->
			<div class="flex flex-col space-y-2">
				<span class="flex h-12 flex-row items-center justify-between">
					<label for="description" class="text-s mb-1 font-medium">
						{$_('new_expense.form.description.label')}
					</label>

					{#if showErrors('description')}
						<span
							class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
						>
							<span>{errors.description![0]}</span>
							<CircleAlert class="size-4" />
						</span>
					{/if}
				</span>

				<input
					class={[
						'h-[2.5em] border-0 bg-base-300 inset-shadow-sm dark:bg-dark-base-300',
						showErrors('description') && 'border-2 border-red-500'
					]}
					id="description"
					type="text"
					name="description"
					onblur={onBlur}
					bind:value={description}
				/>
				<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
					{$_('new_expense.form.description.help')}
				</span>
			</div>
			<div class="flex flex-col space-y-2">
				<span class="flex h-12 flex-row items-center justify-between">
					<label for="date" class="text-s mb-1 font-medium">
						{$_('new_expense.form.date.label')}
					</label>

					{#if showErrors('expense-date')}
						<span
							class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
						>
							<span>{errors['expense-date']![0]}</span>
							<CircleAlert class="size-4" />
						</span>
					{/if}
				</span>

				<input type="hidden" name="expense-date" value={expenseDate?.toString() ?? ''} />
				<DatePicker.Root
					bind:value={expenseDate}
					maxValue={today(getLocalTimeZone())}
					locale={$locale ?? 'sv'}
				>
					<div
						onfocusout={onDateBlur}
						class={[
							'flex h-[2.5em] w-full flex-row items-center bg-base-300 inset-shadow-sm dark:bg-dark-base-300',
							showErrors('expense-date') && 'border-2 border-red-500'
						]}
					>
						<DatePicker.Input class="flex flex-1 px-2">
							{#snippet children({ segments })}
								{#each segments as { part, value }}
									<DatePicker.Segment
										{part}
										class="px-0.5 {part !== 'literal' && /\p{L}/u.test(value)
											? 'text-base-subtle dark:text-dark-base-subtle'
											: ''}"
									>
										{value}
									</DatePicker.Segment>
								{/each}
							{/snippet}
						</DatePicker.Input>
						<DatePicker.Trigger class="px-2 hover:cursor-pointer">
							<CalendarIcon class="size-4" />
						</DatePicker.Trigger>
					</div>
					<DatePicker.Content class="z-50 bg-base-200 p-2 shadow-lg dark:bg-dark-base-200">
						<DatePicker.Calendar>
							{#snippet children({ months, weekdays })}
								<DatePicker.Header class="mb-2 flex items-center justify-between">
									<DatePicker.PrevButton class="p-1 hover:cursor-pointer">
										<ChevronLeft class="size-4" />
									</DatePicker.PrevButton>
									<DatePicker.Heading class="text-sm font-medium" />
									<DatePicker.NextButton class="p-1 hover:cursor-pointer">
										<ChevronRight class="size-4" />
									</DatePicker.NextButton>
								</DatePicker.Header>
								{#each months as month}
									<DatePicker.Grid>
										<DatePicker.GridHead>
											<DatePicker.GridRow class="flex">
												{#each weekdays as day}
													<DatePicker.HeadCell
														class="w-8 text-xs text-base-subtle dark:text-dark-base-subtle"
													>
														{day.slice(0, 2)}
													</DatePicker.HeadCell>
												{/each}
											</DatePicker.GridRow>
										</DatePicker.GridHead>
										<DatePicker.GridBody>
											{#each month.weeks as week}
												<DatePicker.GridRow class="flex">
													{#each week as date}
														<DatePicker.Cell {date} month={month.value}>
															<DatePicker.Day
																class="flex h-8 w-8 items-center justify-center text-sm hover:cursor-pointer hover:bg-base-100 data-disabled:cursor-not-allowed data-disabled:opacity-30 data-outside-month:text-base-subtle data-outside-month:opacity-40 data-selected:bg-money-green-600 data-selected:text-base-100 dark:hover:bg-dark-base-100"
															/>
														</DatePicker.Cell>
													{/each}
												</DatePicker.GridRow>
											{/each}
										</DatePicker.GridBody>
									</DatePicker.Grid>
								{/each}
							{/snippet}
						</DatePicker.Calendar>
					</DatePicker.Content>
				</DatePicker.Root>
				<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
					{$_('new_expense.form.date.help')}
				</span>
			</div>
		</fieldset>

		<fieldset class="flex w-full flex-col p-0">
			<span class="flex h-12 flex-row items-center justify-between">
				<span class="texts mb-1 font-medium">
					{$_('new_expense.form.receipts.label')}
				</span>

				{#if showErrors('files')}
					<span
						class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
					>
						<span>{errors.files![0]}</span>
						<CircleAlert class="size-4" />
					</span>
				{/if}
			</span>
			<div class={['flex flex-1', showErrors('files') && 'border-2 border-red-500']}>
				<FileInput bind:files={receiptFiles} />
			</div>
		</fieldset>
	</div>

	<fieldset class="flex flex-col space-y-2 border-0 p-0">
		<legend class="text-s mb-1 flex flex-row items-center font-medium">
			{$_('new_expense.form.expense_parts.label')}
			<a href="/help/expense-parts" class="group text-money-green-800 dark:text-money-green-600">
				<CircleQuestionMark class="mx-2 size-4 transition-all group-hover:scale-125" />
			</a>
		</legend>

		<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_expense.form.expense_parts.help')}
		</span>

		<!--   Expense parts     -->
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
								onblur={() =>
									(validationResult = validation.run(
										buildValidationData(),
										`part-${i}-costcenter`
									))}
							/>
							{#if showErrors(`part-${i}-costcenter`)}
								<span
									class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
								>
									<span>{errors[`part-${i}-costcenter`]![0]}</span>
									<CircleAlert class="size-4" />
								</span>
							{/if}
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
								onblur={() =>
									(validationResult = validation.run(
										buildValidationData(),
										`part-${i}-secondarycostcenter`
									))}
							/>
							{#if showErrors(`part-${i}-secondarycostcenter`)}
								<span
									class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
								>
									<span>{errors[`part-${i}-secondarycostcenter`]![0]}</span>
									<CircleAlert class="size-4" />
								</span>
							{/if}
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
								onblur={() =>
									(validationResult = validation.run(
										buildValidationData(),
										`part-${i}-budgetline`
									))}
							/>
							{#if showErrors(`part-${i}-budgetline`)}
								<span
									class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
								>
									<span>{errors[`part-${i}-budgetline`]![0]}</span>
									<CircleAlert class="size-4" />
								</span>
							{/if}
						</div>
						<div class="flex flex-col space-y-1">
							{#if i === 0}<span class="mb-1 text-right text-sm font-medium"
									>{$_('new_expense.form.expense_parts.amount_label')}</span
								>{/if}
							<div class="relative flex items-center">
								<input type="hidden" name="part-{i}-amount" value={part.raw ?? ''} />
								<input
									type="text"
									id="part-{i}-amount"
									bind:value={part.display}
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
							{#if showErrors(`part-${i}-amount`)}
								<span
									class="flex flex-row items-center justify-end gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
								>
									<span>{errors[`part-${i}-amount`]![0]}</span>
									<CircleAlert class="size-4" />
								</span>
							{/if}
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
					{$_('new_expense.form.add_part')}
				</span>
			</button>
		</div>

		<input class="hidden" />
	</fieldset>

	<div class="mx-auto flex w-full flex-row justify-between">
		<button type="button" class="cursor-pointer bg-base-300 p-4 dark:bg-dark-base-300">
			{$_('cancel')}
		</button>
		<button
			type="submit"
			class="flex w-72 cursor-pointer bg-money-green-600 p-4 text-dark-base-text hover:bg-money-green-500"
		>
			{#if submitting}
				<CashSpinner />
			{:else}
				<BanknoteArrowUp class="m-2 my-auto" />
				{$_('new_expense.form.submit')}
			{/if}
		</button>
	</div>
</form>
