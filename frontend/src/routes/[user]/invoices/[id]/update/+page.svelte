<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { BanknoteArrowUp, Check, CircleAlert, Copy, Undo2, X } from '@lucide/svelte';
	import { parseDate } from '@internationalized/date';
	import { usePdfiumEngine } from '@embedpdf/engines/svelte';
	import type { PageData } from './$types';
	import type { Invoice } from '$lib/api/types';
	import ReceiptViewer from '$lib/components/ReceiptViewer.svelte';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import DatePicker from '$lib/components/DatePicker.svelte';
	import FileInput from '../../../../invoices/new/FileInput.svelte';
	import FileThumbnail from '$lib/components/FileThumbnail.svelte';
	import ExpenseParts from '$lib/components/ExpenseParts.svelte';
	import validation, { validateFormData } from './validation.ts';
	import type { UpdateInvoiceFormData } from './validation.ts';
	import { untrack } from 'svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { ZERO } from '$lib/money';
	import { api } from '$lib/api/index';
	import { alerts, success } from '$lib/stores/alerts';
	import { goto } from '$app/navigation';
	import { logger } from '$lib/logger';

	let { data }: { data: PageData } = $props();
	let { invoice }: { invoice: Invoice } = $derived(data);

	const pdfium = usePdfiumEngine();

	const partsLocked = $derived(invoice.parts.some((p) => p.attested_by != null));

	let copied = $state(false);
	function copyId() {
		navigator.clipboard.writeText(String(invoice.id));
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	let submitting = $state(false);

	function initialFormData(inv: Invoice): UpdateInvoiceFormData {
		return {
			description: inv.description,
			files: [],
			deletedFiles: new SvelteSet<number>(),
			parts:
				inv.parts.length > 0
					? inv.parts.map((p) => ({
							cost_centre: p.cost_centre,
							secondary_cost_centre: p.secondary_cost_centre,
							budget_line: p.budget_line,
							amount: p.amount
						}))
					: [
							{
								cost_centre: '',
								secondary_cost_centre: '',
								budget_line: '',
								amount: ZERO
							}
						],
			invoiceDate: inv.invoice_date ? parseDate(inv.invoice_date) : undefined,
			dueDate: inv.due_date ? parseDate(inv.due_date) : undefined
		};
	}

	let formData: UpdateInvoiceFormData = $state(untrack(() => initialFormData(data.invoice)));

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		submitting = true;
		validationResult = validation.run(formData);
		if (!validationResult.isValid()) {
			submitting = false;
			return;
		}

		const updated = await api.invoices.update(invoice.id, validateFormData(formData, !partsLocked));
		logger.debug(updated, 'invoice updated');

		alerts.update((alerts) => [...alerts, success($_('invoice_updated'))]);
		await goto(`/${invoice.owner.username}/invoices/${invoice.id}`);
	}

	let validationResult = $state(validation.get());
	let errors = $derived(validationResult.getErrors());

	function onBlur(e: FocusEvent & { currentTarget: HTMLInputElement }) {
		validationResult = validation.run(formData, e.currentTarget.name);
	}

	function onInvoiceDateBlur() {
		validationResult = validation.run(formData, 'invoice-date');
	}

	function onDueDateBlur() {
		validationResult = validation.run(formData, 'due-date');
	}

	function validateField(field: string) {
		validationResult = validation.run(formData, field);
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
		<ExpenseParts
			bind:parts={formData.parts}
			{errors}
			{showErrors}
			onValidate={validateField}
			addPartPrompt={$_('new_invoice.form.invoice_parts.add_part')}
		/>
	</div>

	<div class="flex flex-col gap-4 lg:flex-row">
		<div class="flex max-h-256 flex-col lg:w-2/5">
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
						bind:value={formData.description}
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

					<input type="hidden" name="invoice-date" value={formData.invoiceDate?.toString() ?? ''} />
					<DatePicker
						bind:value={formData.invoiceDate}
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

					<input type="hidden" name="due-date" value={formData.dueDate?.toString() ?? ''} />
					<DatePicker
						bind:value={formData.dueDate}
						invalid={showErrors('due-date')}
						errors={errors['due-date']}
						onBlur={onDueDateBlur}
					/>
				</div>

				<div class="flex flex-col space-y-2">
					<span class="text-s mb-1 font-medium">
						{$_('new_invoice.form.files.label')}
					</span>
					<div class="flex flex-wrap justify-between gap-2 bg-base-300 p-2 dark:bg-dark-base-300">
						<input
							type="hidden"
							name="deleteFiles"
							value={JSON.stringify([...formData.deletedFiles])}
						/>
						{#each invoice.files as file}
							{@const isDeleted = formData.deletedFiles.has(file.id)}
							<div
								class="mx-4 flex w-full flex-row space-x-4 border-b border-base-600 dark:border-b-dark-base-200"
							>
								<FileThumbnail
									source={file.file}
									engine={pdfium.engine}
									class={isDeleted ? 'h-12 w-9 opacity-50' : 'h-12 w-9'}
								/>
								<div class="flex flex-1 flex-col">
									<span class={['my-auto', isDeleted && 'opacity-50']}>
										{decodeURIComponent(new URL(file.file).pathname.split('/').pop() ?? '')}
									</span>
								</div>
								<button
									type="button"
									class="ml-auto text-base-subtle transition-all hover:scale-115 hover:cursor-pointer dark:text-dark-base-subtle"
									onclick={isDeleted
										? () => formData.deletedFiles.delete(file.id)
										: () => formData.deletedFiles.add(file.id)}
								>
									{#if isDeleted}
										<Undo2 />
									{:else}
										<X />
									{/if}
								</button>
							</div>
						{/each}
					</div>
					<div class="flex h-56">
						<FileInput bind:files={formData.files} engine={pdfium.engine} />
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
