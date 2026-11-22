<!--
@component
The owner's edit form for a claim.
-->
<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { getLocalTimeZone, parseDate, today } from '@internationalized/date';
	import { SvelteSet } from 'svelte/reactivity';
	import type { Expense, Invoice } from '#lib/api/types.ts';
	import ReceiptLayout from '#lib/components/ReceiptLayout.svelte';
	import TextField from '#lib/components/TextField.svelte';
	import DateField from '#lib/components/DateField.svelte';
	import FileInput from '#lib/components/FileInput.svelte';
	import FormActions from '#lib/components/FormActions.svelte';
	import UnsavedChanges from '#lib/components/UnsavedChanges.svelte';
	import ExpenseParts, { editableParts } from '#lib/components/ExpenseParts.svelte';
	import { CopyableValue, PageHeader, Field, Section } from '#lib/components/ui/index.ts';
	import { formValidation } from '#lib/formValidation.svelte.ts';
	import { submitter } from '#lib/submit.svelte.ts';
	import { success } from '#lib/stores/alerts.ts';
	import { claimIdLabel } from '#lib/claimId.ts';
	import { api } from '#lib/api/index.ts';
	import expenseValidation, {
		validateFormData as expensePayload,
		type UpdateExpenseFormData
	} from './expenses/[id]/update/validation';
	import invoiceValidation, {
		validateFormData as invoicePayload,
		type UpdateInvoiceFormData
	} from './invoices/[id]/update/validation';

	let { kind, claim }: { kind: 'expense' | 'invoice'; claim: Expense | Invoice } = $props();

	const partsLocked = $derived(claim.parts.some((p) => p.attested_by != null));

	const day = (date: string | null) => (date ? parseDate(date) : undefined);

	// Only the kind's own date fields are set
	// svelte-ignore state_referenced_locally
	let formData: UpdateExpenseFormData & UpdateInvoiceFormData = $state({
		description: claim.description,
		files: [],
		deletedFiles: new SvelteSet<number>(),
		budgetUsage: [],
		parts: editableParts(claim.parts),
		date: day('expense_date' in claim ? claim.expense_date : null),
		invoiceDate: day('invoice_date' in claim ? claim.invoice_date : null),
		dueDate: day('due_date' in claim ? claim.due_date : null)
	});

	const submit = submitter(async () => {
		if (!form.validate()) return;
		const payload = (kind === 'invoice' ? invoicePayload : expensePayload)(formData, !partsLocked);
		await api[`${kind}s`].update(claim.id, payload);
		success($_(`${kind}_updated`));
		return `/${claim.owner.username}/${kind}s/${claim.id}`;
	});

	// svelte-ignore state_referenced_locally
	const form =
		kind === 'invoice'
			? formValidation(invoiceValidation, () => formData)
			: formValidation(expenseValidation, () => formData);
</script>

<UnsavedChanges data={() => formData} {submit} />

<form onsubmit={submit.onsubmit} class="flex flex-col gap-8">
	<ReceiptLayout files={claim.files.map((f) => f.file)}>
		{#snippet header()}
			<PageHeader title={claim.description} small class="pb-0" />
			<div class="flex flex-wrap items-center gap-1.5">
				<CopyableValue display={claimIdLabel(claim, $_)} value={claim.id} />
				<CopyableValue display={`${claim.owner.first_name} ${claim.owner.last_name}`} />
			</div>
		{/snippet}
		<TextField
			name="description"
			label={$_('new_expense.form.description.label')}
			{form}
			bind:value={formData.description}
		/>

		{#if kind === 'invoice'}
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
		{:else}
			<DateField
				name="expense-date"
				label={$_('new_expense.form.date.label')}
				maxValue={today(getLocalTimeZone())}
				{form}
				bind:value={formData.date}
			/>
		{/if}

		<Field
			label={$_(
				kind === 'invoice' ? 'new_invoice.form.files.label' : 'new_expense.form.receipts.label'
			)}
			for="files"
		>
			<FileInput
				bind:files={formData.files}
				existing={claim.files}
				deleted={formData.deletedFiles}
			/>
		</Field>

		<Section
			title={$_(kind === 'invoice' ? 'new_invoice.form.invoice_parts.label' : 'expense_parts')}
		>
			<ExpenseParts
				bind:parts={formData.parts}
				bind:budgetUsage={formData.budgetUsage}
				errorFor={form.errorFor}
				onValidate={form.validate}
				addPartPrompt={$_(
					kind === 'invoice'
						? 'new_invoice.form.invoice_parts.add_part'
						: 'new_expense.form.add_part'
				)}
			/>
		</Section>

		<FormActions
			cancelHref="/{claim.owner.username}/{kind}s/{claim.id}"
			submitLabel={$_('submit')}
			submitting={submit.submitting}
		/>
	</ReceiptLayout>
</form>
