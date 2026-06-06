<script lang="ts">
	import FileInput from './FileInput.svelte';
	import { _ } from 'svelte-i18n';
	import { BanknoteArrowUp, CircleAlert, CircleQuestionMark } from '@lucide/svelte';
	import { type DateValue, getLocalTimeZone, today } from '@internationalized/date';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import ExpenseParts, { type Part, newPart } from '$lib/components/ExpenseParts.svelte';
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

	let submitting: Boolean = $state(false);
	let description = $state('');
	let receiptFiles: File[] = $state([]);
	let parts: Part[] = $state([newPart()]);
	let expenseDate: DateValue | undefined = $state();

	function buildValidationData() {
		return {
			description,
			'expense-date': expenseDate?.toString(),
			files: receiptFiles,
			parts: parts.map((p) => ({
				costcenter: p.costcenter,
				secondarycostcenter: p.secondarycostcenter,
				budgetline: p.budgetline,
				amount: p.amountRaw
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
		validationResult = validation.run(buildValidationData(), e.currentTarget.name);
	}

	function onDateBlur(e: FocusEvent) {
		// const wrapper = e.currentTarget as HTMLElement;
		// if (e.relatedTarget && wrapper.contains(e.relatedTarget as Node)) return;
		console.log('date blur');
		console.log(e.currentTarget);
		validationResult = validation.run(buildValidationData(), 'expense-date');
	}

	function validateField(field: string) {
		validationResult = validation.run(buildValidationData(), field);
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
							<span>{$_(errors.description![0])}</span>
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
							<span>{$_(errors['expense-date']![0])}</span>
							<CircleAlert class="size-4" />
						</span>
					{/if}
				</span>

				<input type="hidden" name="expense-date" value={expenseDate?.toString() ?? ''} />
				<DatePicker
					bind:value={expenseDate}
					maxValue={today(getLocalTimeZone())}
					invalid={showErrors('expense-date')}
					errors={errors['expense-date']}
					onBlur={onDateBlur}
				/>

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
						<span>{$_(errors.files![0])}</span>
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
		<ExpenseParts
			bind:parts
			{costCenters}
			{budgetLines}
			{errors}
			{showErrors}
			onValidate={validateField}
			addPartPrompt={$_('new_expense.form.add_part')}
		/>

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
