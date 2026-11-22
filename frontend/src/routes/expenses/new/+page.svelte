<script lang="ts">
	import FileInput from '#lib/components/FileInput.svelte';
	import ReceiptSplit from '#lib/components/ReceiptSplit.svelte';
	import FormActions from '#lib/components/FormActions.svelte';
	import { _ } from 'svelte-i18n';
	import { getLocalTimeZone, today } from '@internationalized/date';
	import { Field, Section } from '#lib/components/ui/index.ts';
	import TextField from '#lib/components/TextField.svelte';
	import DateField from '#lib/components/DateField.svelte';
	import ExpenseParts, { newPart } from '#lib/components/ExpenseParts.svelte';
	import { formValidation } from '#lib/formValidation.svelte.ts';
	import validation, { validateFormData } from './validation.ts';
	import type { NewExpenseFormData } from './validation.ts';
	import { api } from '#lib/api/index.ts';
	import { success } from '#lib/stores/alerts.ts';
	import { submitter } from '#lib/submit.svelte.ts';
	import UnsavedChanges from '#lib/components/UnsavedChanges.svelte';

	let formData: NewExpenseFormData = $state({
		description: '',
		files: [],
		budgetUsage: [],
		parts: [newPart()],
		date: undefined
	});

	const submit = submitter(async () => {
		if (!form.validate()) return;
		await api.expenses.create(validateFormData(formData));
		success($_('expense_created'));
		return `/claims/`;
	});

	let pinned = $state<File | null>(null);
	const form = formValidation(validation, () => formData);
</script>

<UnsavedChanges data={() => formData} {submit} />

<ReceiptSplit bind:file={pinned}>
	<form onsubmit={submit.onsubmit} class="@container flex flex-col gap-8">
		<div class="grid gap-6 @3xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
			<div class="flex flex-col gap-6">
				<TextField
					name="description"
					label={$_('new_expense.form.description.label')}
					help={$_('new_expense.form.description.help')}
					{form}
					bind:value={formData.description}
				/>
				<DateField
					name="expense-date"
					label={$_('new_expense.form.date.label')}
					help={$_('new_expense.form.date.help')}
					maxValue={today(getLocalTimeZone())}
					{form}
					bind:value={formData.date}
				/>
			</div>

			<Field
				label={$_('new_expense.form.receipts.label')}
				for="files"
				error={form.errorFor('files')}
			>
				<FileInput bind:files={formData.files} bind:pinned invalid={form.showErrors('files')} />
			</Field>
		</div>

		<Section
			title={$_('new_expense.form.expense_parts.label')}
			description={$_('new_expense.form.expense_parts.help')}
		>
			<ExpenseParts
				bind:parts={formData.parts}
				bind:budgetUsage={formData.budgetUsage}
				errorFor={form.errorFor}
				onValidate={form.validate}
				addPartPrompt={$_('new_expense.form.add_part')}
			/>
		</Section>

		<FormActions
			cancelHref="/claims"
			submitLabel={$_('new_expense.form.submit')}
			submitting={submit.submitting}
		/>
	</form>
</ReceiptSplit>
