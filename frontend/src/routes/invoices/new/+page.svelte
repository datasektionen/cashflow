<script lang="ts">
	import FileInput from '#lib/components/FileInput.svelte';
	import ReceiptSplit from '#lib/components/ReceiptSplit.svelte';
	import FormActions from '#lib/components/FormActions.svelte';
	import { _ } from 'svelte-i18n';
	import { Field, Section } from '#lib/components/ui/index.ts';
	import ExpenseParts, { newPart } from '#lib/components/ExpenseParts.svelte';
	import TextField from '#lib/components/TextField.svelte';
	import DateField from '#lib/components/DateField.svelte';
	import { formValidation } from '#lib/formValidation.svelte.ts';
	import validation, { validateFormData } from './validation.ts';
	import type { NewInvoiceFormData } from './validation.ts';
	import { api } from '#lib/api/index.ts';
	import { success } from '#lib/stores/alerts.ts';
	import { submitter } from '#lib/submit.svelte.ts';
	import UnsavedChanges from '#lib/components/UnsavedChanges.svelte';

	let disclaimerParts = $derived($_('new_invoice.disclaimer').split('{new_expense_link}'));

	let formData: NewInvoiceFormData = $state({
		description: '',
		files: [],
		budgetUsage: [],
		parts: [newPart()],
		invoiceDate: undefined,
		invoiceNumber: '',
		dueDate: undefined
	});

	const submit = submitter(async () => {
		if (!form.validate()) return;
		await api.invoices.create(validateFormData(formData));
		success($_('invoice_created'));
		return `/claims/`;
	});

	let pinned = $state<File | null>(null);
	const form = formValidation(validation, () => formData);
</script>

<UnsavedChanges data={() => formData} {submit} />

<ReceiptSplit bind:file={pinned}>
	<form onsubmit={submit.onsubmit} class="@container flex flex-col gap-8">
		<p class="text-sm text-muted-foreground">
			{disclaimerParts[0]}<a
				href="/expenses/new"
				class="font-medium text-primary-text underline underline-offset-4"
				>{$_('new_invoice.disclaimer_link_text')}</a
			>{disclaimerParts[1]}
		</p>

		<div class="grid gap-6 @3xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
			<div class="flex flex-col gap-6">
				<TextField
					name="description"
					label={$_('new_expense.form.description.label')}
					help={$_('new_invoice.form.description.help')}
					{form}
					bind:value={formData.description}
				/>
				<TextField
					name="invoice-number"
					label={$_('new_invoice.form.invoice_number.label')}
					help={$_('new_invoice.form.invoice_number.help')}
					{form}
					bind:value={formData.invoiceNumber}
				/>
				<div class="grid gap-6 sm:grid-cols-2">
					<DateField
						name="invoice-date"
						label={$_('new_invoice.form.invoice_date.label')}
						{form}
						bind:value={formData.invoiceDate}
					/>
					<DateField
						name="due-date"
						label={$_('new_invoice.form.due_date.label')}
						{form}
						bind:value={formData.dueDate}
					/>
				</div>
			</div>

			<Field label={$_('new_invoice.form.files.label')} for="files" error={form.errorFor('files')}>
				<FileInput bind:files={formData.files} bind:pinned invalid={form.showErrors('files')} />
			</Field>
		</div>

		<Section
			title={$_('new_invoice.form.invoice_parts.label')}
			description={$_('new_invoice.form.invoice_parts.help')}
		>
			<ExpenseParts
				bind:parts={formData.parts}
				bind:budgetUsage={formData.budgetUsage}
				errorFor={form.errorFor}
				onValidate={form.validate}
				addPartPrompt={$_('new_invoice.form.invoice_parts.add_part')}
			/>
		</Section>

		<FormActions
			cancelHref="/claims"
			submitLabel={$_('new_invoice.form.submit')}
			submitting={submit.submitting}
		/>
	</form>
</ReceiptSplit>
