<script lang="ts">
	import { getLocalTimeZone, today } from '@internationalized/date';
	import FileInput from './FileInput.svelte';
	import { _ } from 'svelte-i18n';
	import { BanknoteArrowUp, CircleAlert, CircleQuestionMark } from '@lucide/svelte';
	import { type DateValue } from '@internationalized/date';
	import CashSpinner from '$lib/CashSpinner.svelte';
	import { Label, RadioGroup } from 'bits-ui';
	import ExpenseParts, { newPart, type Part } from '$lib/components/ExpenseParts.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
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

	let disclaimerParts = $derived($_('new_invoice.disclaimer').split('{new_expense_link}'));

	let submitting: Boolean = $state(false);
	let description = $state('');
	let invoiceFiles: File[] = $state([]);
	let invoiceParts: Part[] = $state([newPart()]);
	let invoiceDate: DateValue | undefined = $state();
	let isAccounted: boolean = $state(false);
	let voucherNumber: string = $state('');
	let dueDate: DateValue | undefined = $state();

	function buildValidationData() {
		return {
			description,
			'invoice-date': invoiceDate?.toString(),
			files: invoiceFiles,
			parts: invoiceParts.map((p) => ({
				costcenter: p.costcenter,
				secondarycostcenter: p.secondarycostcenter,
				budgetline: p.budgetline,
				amount: p.amountRaw
			}))
		};
	}

	function handleSubmit(e: SubmitEvent) {
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

	// function onDateBlur(e: FocusEvent) {
	// 	validationResult = validation.run(buildValidationData(), 'expense-date');
	// }

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
	<!-- Make sure the user is using the correct form -->
	<div class="flex flex-col space-y-2">
		<p>
			{disclaimerParts[0]}<a
				href="/expenses/new"
				class="text-money-green-800 underline dark:text-money-green-500"
				>{$_('new_invoice.disclaimer_link_text')}</a
			>{disclaimerParts[1]}
		</p>

		<RadioGroup.Root class="flex flex-col gap-4 text-sm">
			<div class="flex flex-row items-center space-x-2">
				<RadioGroup.Item
					id="paid-no"
					value="paid-no"
					class={[
						'border border-base-800 bg-base-500 inset-shadow-xs',
						'data-[state=checked]:border-4 data-[state=checked]:border-money-green-500 data-[state=checked]:bg-white',
						'size-4 cursor-pointer',
						'dark:border-dark-base-50 dark:bg-dark-base-200',
						'dark:data-[state=checked]:bg-dark-base-200'
					]}
				/>
				<Label.Root for="paid-no">Nej, sektionen ska göra det</Label.Root>
			</div>
			<div class="flex flex-row items-center space-x-2">
				<RadioGroup.Item
					id="paid-yes"
					value="paid-yes"
					class={[
						'border border-base-800 bg-base-500 inset-shadow-xs',
						'data-[state=checked]:border-4 data-[state=checked]:border-money-green-500 data-[state=checked]:bg-white',
						'size-4 cursor-pointer',
						'dark:border-dark-base-50 dark:bg-dark-base-200',
						'dark:data-[state=checked]:bg-dark-base-200'
					]}
				/>
				<Label.Root for="paid-yes">Ja, från sektionens konto</Label.Root>
			</div>
		</RadioGroup.Root>
	</div>

	<div class="flex flex-col justify-between space-y-6 lg:max-h-128 lg:flex-row lg:space-x-6">
		<fieldset class="flex flex-col space-y-6 border-0 p-0">
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
					{$_('new_invoice.form.description.help')}
				</span>
			</div>

			<div class="flex flex-col space-y-2">
				<label for="invoice-date" class="text-s mb-1 font-medium"> Fakturadatum </label>
				<DatePicker maxValue={today(getLocalTimeZone())} />
			</div>
			<div class="flex flex-col space-y-2">
				<label for="due-date" class="text-s mb-1 font-medium"> Förfallodatum </label>
				<DatePicker minValue={today(getLocalTimeZone())} />
			</div>
		</fieldset>

		<fieldset class="flex w-full flex-col p-0">
			<span class="flex h-12 flex-row items-center justify-between">
				<span class="texts mb-1 font-medium">
					{$_('new_invoice.form.files.label')}
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
				<FileInput bind:files={invoiceFiles} />
			</div>
		</fieldset>
	</div>

	<fieldset class="flex flex-col space-y-2 border-0 p-0">
		<legend class="text-s mb-1 flex flex-row items-center font-medium">
			{$_('new_invoice.form.invoice_parts.label')}
			<a href="/help/expense-parts" class="group text-money-green-800 dark:text-money-green-600">
				<CircleQuestionMark class="mx-2 size-4 transition-all group-hover:scale-125" />
			</a>
		</legend>

		<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_invoice.form.invoice_parts.help')}
		</span>

		<ExpenseParts
			bind:parts={invoiceParts}
			{costCenters}
			{budgetLines}
			{errors}
			{showErrors}
			onValidate={validateField}
			addPartPrompt={$_('new_invoice.form.invoice_parts.add_part')}
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
				{$_('new_invoice.form.submit')}
			{/if}
		</button>
	</div>
</form>
