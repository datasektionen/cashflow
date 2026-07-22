<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { BanknoteArrowUp, Check, CircleAlert, Copy } from '@lucide/svelte';
	import { parseDate, type DateValue } from '@internationalized/date';
	import type { PageData } from './$types';
	import type { Invoice } from '$lib/api/types.ts';
	import ReceiptViewer from '$lib/components/ReceiptViewer.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import FileInput from '../../../../invoices/new/FileInput.svelte';
	import ExpenseParts, { type Part, newPart } from '$lib/components/ExpenseParts.svelte';
	import validation from './validation.ts';

	let { data }: { data: PageData } = $props();
	let { invoice }: { invoice: Invoice } = data;

	const partsLocked = invoice.parts.some((p) => p.attested_by != null);

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});
	const totalAmount = $derived(
		fmt.format(
			invoice.parts.reduce(
				(sum: number, part: { amount: string }) => sum + parseFloat(part.amount),
				0
			)
		)
	);

	let copied = $state(false);
	function copyId() {
		navigator.clipboard.writeText(String(invoice.id));
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	let submitting = $state(false);
	let description = $state(invoice.description);
	let newFiles: File[] = $state([]);
	let invoiceDate: DateValue | undefined = $state(
		invoice.invoice_date ? parseDate(invoice.invoice_date) : undefined
	);
	let dueDate: DateValue | undefined = $state(
		invoice.due_date ? parseDate(invoice.due_date) : undefined
	);
	let parts: Part[] = $state(
		invoice.parts.length > 0
			? invoice.parts.map((p) => {
					const amountRaw = parseFloat(p.amount);
					return {
						amountRaw,
						amountDisplay: fmt.format(amountRaw),
						costcenter: p.cost_centre,
						secondarycostcenter: p.secondary_cost_centre,
						budgetline: p.budget_line
					};
				})
			: [newPart()]
	);

	function buildValidationData() {
		return {
			description,
			'invoice-date': invoiceDate?.toString(),
			'due-date': dueDate?.toString(),
			parts: partsLocked
				? []
				: parts.map((p) => ({
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

	function onInvoiceDateBlur() {
		validationResult = validation.run(buildValidationData(), 'invoice-date');
	}

	function onDueDateBlur() {
		validationResult = validation.run(buildValidationData(), 'due-date');
	}

	function validateField(field: string) {
		validationResult = validation.run(buildValidationData(), field);
	}

	function showErrors(field: string) {
		return validationResult.isTested(field) && (errors[field]?.length ?? 0) > 0;
	}
</script>

<div class="mb-6 flex flex-wrap items-center gap-3">
	<div class="flex items-center gap-2 text-sm text-base-subtle dark:text-dark-base-subtle">
		<button
			onclick={copyId}
			class="flex cursor-pointer items-center gap-1 transition-colors hover:text-base-text dark:hover:text-dark-base-text"
		>
			<span>{$_('invoice')} #{invoice.id}</span>
			{#if copied}
				<Check class="size-3" />
			{:else}
				<Copy class="size-3" />
			{/if}
		</button>
		<span>·</span>
		<span>{invoice.owner.first_name} {invoice.owner.last_name}</span>
	</div>
</div>

<form
	method="POST"
	enctype="multipart/form-data"
	onsubmit={handleSubmit}
	class="flex flex-col gap-8"
>
	<div class="flex w-full flex-col space-y-2">
		<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
		{#if partsLocked}
			<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
				{$_('expense_parts_locked')}
			</span>
			<PartsTable parts={invoice.parts} owner={invoice.owner} {totalAmount} />
		{:else}
			<ExpenseParts
				bind:parts
				{errors}
				{showErrors}
				onValidate={validateField}
				addPartPrompt={$_('new_invoice.form.invoice_parts.add_part')}
			/>
		{/if}
	</div>

	<div class="flex flex-col gap-4 lg:flex-row">
		<div class="flex max-h-256 flex-col border lg:w-2/5">
			{#if invoice.files.length > 0}
				<ReceiptViewer source={invoice.files.map((f) => f.file)} />
			{:else}
				<div
					class="flex flex-1 items-center justify-center p-8 text-sm text-base-subtle dark:text-dark-base-subtle"
				>
					{$_('expense_no_files')}
				</div>
			{/if}
		</div>

		<div class="flex flex-col gap-12 lg:w-3/5 lg:pt-1 xl:pr-16">
			<div class="flex flex-col space-y-6">
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
				</div>

				<div class="flex flex-col space-y-2">
					<span class="flex h-12 flex-row items-center justify-between">
						<label for="invoice-date" class="text-s mb-1 font-medium">
							{$_('new_invoice.form.invoice_date.label')}
						</label>

						{#if showErrors('invoice-date')}
							<span
								class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
							>
								<span>{$_(errors['invoice-date']![0])}</span>
								<CircleAlert class="size-4" />
							</span>
						{/if}
					</span>

					<input type="hidden" name="invoice-date" value={invoiceDate?.toString() ?? ''} />
					<DatePicker
						bind:value={invoiceDate}
						invalid={showErrors('invoice-date')}
						errors={errors['invoice-date']}
						onBlur={onInvoiceDateBlur}
					/>
				</div>

				<div class="flex flex-col space-y-2">
					<span class="flex h-12 flex-row items-center justify-between">
						<label for="due-date" class="text-s mb-1 font-medium">
							{$_('new_invoice.form.due_date.label')}
						</label>

						{#if showErrors('due-date')}
							<span
								class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
							>
								<span>{$_(errors['due-date']![0])}</span>
								<CircleAlert class="size-4" />
							</span>
						{/if}
					</span>

					<input type="hidden" name="due-date" value={dueDate?.toString() ?? ''} />
					<DatePicker
						bind:value={dueDate}
						invalid={showErrors('due-date')}
						errors={errors['due-date']}
						onBlur={onDueDateBlur}
					/>
				</div>

				<div class="flex flex-col space-y-2">
					<span class="text-s mb-1 font-medium">
						{$_('new_invoice.form.files.label')}
					</span>
					<div class="flex h-56">
						<FileInput bind:files={newFiles} />
					</div>
				</div>
			</div>
		</div>
	</div>

	<div class="flex w-full flex-row justify-between">
		<a
			href="/{invoice.owner.username}/invoices/{invoice.id}"
			class="flex cursor-pointer items-center bg-base-300 p-4 dark:bg-dark-base-300"
		>
			{$_('cancel')}
		</a>
		<button
			type="submit"
			class="flex w-72 cursor-pointer items-center justify-center bg-money-green-600 p-4 text-dark-base-text hover:bg-money-green-500"
		>
			{#if submitting}
				<CashSpinner />
			{:else}
				<BanknoteArrowUp class="m-2 my-auto" />
				{$_('submit')}
			{/if}
		</button>
	</div>
</form>
