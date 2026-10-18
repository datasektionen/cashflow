<script lang="ts">
	import FileInput from './FileInput.svelte';
	import { _ } from 'svelte-i18n';
	import { BanknoteArrowUp, CircleAlert } from '@lucide/svelte';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import ExpenseParts from '$lib/components/ExpenseParts.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import validation, { validateFormData } from './validation.ts';
	import type { NewInvoiceFormData } from './validation.ts';
	import { api } from '$lib/api/index';
	import { alerts, success } from '$lib/stores/alerts';
	import { goto } from '$app/navigation';
	import { logger } from '$lib/logger';
	import { ZERO } from '$lib/money';

	let disclaimerParts = $derived($_('new_invoice.disclaimer').split('{new_expense_link}'));
	let submitting: Boolean = $state(false);

	let formData: NewInvoiceFormData = $state({
		description: '',
		files: [],
		budgetUsage: [],
		parts: [
			{
				cost_centre: '',
				secondary_cost_centre: '',
				budget_line: '',
				amount: ZERO
			}
		],
		invoiceDate: undefined,
		invoiceNumber: '',
		dueDate: undefined
	});

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		submitting = true;
		validationResult = validation.run(formData);
		if (!validationResult.isValid()) {
			submitting = false;
			return;
		}

		const created = await api.invoices.create(validateFormData(formData));
		logger.debug(created, 'new invoice created');

		alerts.update((alerts) => [...alerts, success($_('invoice_created'))]);
		await goto(`/claims/`);
	}

	let validationResult = $state(validation.get());
	let errors = $derived(validationResult.getErrors());
	let warnings = $derived(validationResult.getWarnings());

	function onBlur(e: FocusEvent & { currentTarget: HTMLInputElement }) {
		validationResult = validation.run(formData, e.currentTarget.name);
	}

	function validateField(field: string) {
		validationResult = validation.run(formData, field);
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
					bind:value={formData.description}
				/>
				<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
					{$_('new_invoice.form.description.help')}
				</span>
			</div>

			<div class="flex flex-col space-y-2">
				<span class="flex h-12 flex-row items-center justify-between">
					<label for="invoice-number" class="text-s mb-1 font-medium">
						{$_('new_invoice.form.invoice_number.label')}
					</label>

					{#if showErrors('invoice-number')}
						<span
							class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
						>
							<span>{$_(errors['invoice-number']![0])}</span>
							<CircleAlert class="size-4" />
						</span>
					{/if}
				</span>

				<input
					class={[
						'h-[2.5em] border-0 bg-base-300 inset-shadow-sm dark:bg-dark-base-300',
						showErrors('invoice-number') && 'border-2 border-red-500'
					]}
					id="invoice-number"
					type="text"
					name="invoice-number"
					onblur={onBlur}
					bind:value={formData.invoiceNumber}
				/>
				<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
					{$_('new_invoice.form.invoice_number.help')}
				</span>
			</div>

			<div class="flex flex-col space-y-2">
				<label for="invoice-date" class="text-s mb-1 font-medium"> Fakturadatum </label>
				<input type="hidden" name="invoice-date" value={formData.invoiceDate?.toString() ?? ''} />
				<DatePicker
					bind:value={formData.invoiceDate}
					invalid={showErrors('invoice-date')}
					errors={errors['invoice-date']}
					onBlur={() => validateField('invoice-date')}
				/>
			</div>
			<div class="flex flex-col space-y-2">
				<label for="due-date" class="text-s mb-1 font-medium"> Förfallodatum </label>
				<input type="hidden" name="due-date" value={formData.dueDate?.toString() ?? ''} />
				<DatePicker
					bind:value={formData.dueDate}
					invalid={showErrors('due-date')}
					errors={errors['due-date']}
					onBlur={() => validateField('due-date')}
				/>
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
				<FileInput bind:files={formData.files} />
			</div>
		</fieldset>
	</div>

	<fieldset class="flex flex-col space-y-2 border-0 p-0">
		<legend class="text-s mb-1 flex flex-row items-center font-medium">
			{$_('new_invoice.form.invoice_parts.label')}
		</legend>

		<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_invoice.form.invoice_parts.help')}
		</span>

		<ExpenseParts
			bind:parts={formData.parts}
			bind:budgetUsage={formData.budgetUsage}
			{errors}
			{warnings}
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
