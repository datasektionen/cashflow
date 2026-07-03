<script lang="ts">
	import { _, locale } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import type { PageData } from './$types';
	import { api } from '$lib/api';
	import { isErrorResponse } from '$lib/api/errors';
	import { alerts, error, success } from '$lib/stores/alerts';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import CommentDisplay from '$lib/components/CommentDisplay.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import VoucherRowFields, { draftsFromParts, toVoucherRows } from '../../VoucherRowFields.svelte';
	import type { VoucherRowDraft } from '../../VoucherRowFields.svelte';

	let { data }: { data: PageData } = $props();
	const invoice = $derived(data.invoice);

	// Prefill once; the form must not reset if data refreshes while editing.
	// svelte-ignore state_referenced_locally
	let voucherRows = $state<VoucherRowDraft[]>(
		draftsFromParts(data.invoice.parts, data.invoice.recommended_credit_account)
	);
	let voucherNumber = $state('');
	// Which of the two submit buttons is in flight, so only it shows a spinner.
	let submitting = $state<'rows' | 'number' | null>(null);

	const isAccounted = $derived(invoice.verification != null && invoice.verification !== '');

	async function submitAccounting(
		kind: 'rows' | 'number',
		payload: Parameters<typeof api.invoices.account>[1]
	) {
		submitting = kind;
		try {
			const updated = await api.invoices.account(invoice.id, payload);
			alerts.update((a) => [
				...a,
				success($_('admin_account.success', { values: { verification: updated.verification } }))
			]);
			// Back to the queue of remaining accountable invoices.
			await goto('/admin/account/invoices');
		} catch (e) {
			const message = isErrorResponse(e) ? e.detail : $_('admin_account.error');
			alerts.update((a) => [...a, error(message)]);
		} finally {
			submitting = null;
		}
	}

	function submitVoucherRows() {
		submitAccounting('rows', { voucher_rows: toVoucherRows(voucherRows) });
	}

	// Rows without an account are dropped on submit, so require at least one.
	const hasSubmittableRows = $derived(toVoucherRows(voucherRows).length > 0);

	function submitVoucherNumber() {
		submitAccounting('number', { voucher_number: voucherNumber.trim() });
	}

	const isAttested = $derived(
		invoice.parts.length > 0 && invoice.parts.every((p) => p.attested_by != null)
	);
</script>

<div class="mb-6 flex flex-wrap items-center gap-3">
	<div class="flex items-center gap-2 text-sm text-base-subtle dark:text-dark-base-subtle">
		<span>{$_('invoice')} #{invoice.id}</span>
		<span>·</span>
		<span>{invoice.owner.first_name} {invoice.owner.last_name}</span>
	</div>
	<div class="flex items-center gap-2">
		{#if isAttested}
			<span
				class="bg-money-green-200 px-2.5 py-0.5 text-xs font-semibold text-money-green-900 dark:bg-money-green-600 dark:text-white"
				>{$_('expense_attested')}</span
			>
		{/if}
		{#if invoice.confirmed_at}
			<span
				class="dark:text-money-green-950 bg-money-green-500 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-400"
				>{$_('expense_confirmed')}</span
			>
		{/if}
		{#if invoice.paid_at}
			<span
				class="dark:text-money-green-950 bg-money-green-700 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-300"
				>{$_('expense_paid')}</span
			>
		{/if}
		{#if invoice.verification}
			<span
				class="bg-money-green-900 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-200 dark:text-money-green-900"
				>{invoice.verification}</span
			>
		{/if}
	</div>
</div>

<div class="flex flex-col gap-10">
	<div class="flex flex-col gap-8 lg:flex-row">
		<div class="flex flex-col gap-8 lg:w-3/5 lg:pt-1">
			<div>
				<h2 class="mb-2 text-base font-semibold">{$_('admin_account.create_voucher')}</h2>
				<VoucherRowFields
					bind:voucherRows
					accounts={data.accounts}
					costCentres={data.costCentres}
				/>
				<div class="mt-4 flex justify-end">
					<button
						type="button"
						onclick={submitVoucherRows}
						disabled={submitting != null || isAccounted || !hasSubmittableRows}
						class="flex min-w-24 cursor-pointer justify-center bg-money-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-money-green-500 disabled:cursor-not-allowed disabled:opacity-50"
					>
						{#if submitting === 'rows'}
							<CashSpinner class="size-5" />
						{:else}
							{$_('submit')}
						{/if}
					</button>
				</div>
			</div>

			<div class="border-t border-base-400 pt-6 dark:border-dark-base-200">
				<h2 class="mb-2 text-base font-semibold">{$_('admin_account.existing_voucher')}</h2>
				<div class="flex gap-2">
					<input
						type="text"
						bind:value={voucherNumber}
						placeholder={$_('admin_account.voucher_number_placeholder')}
						class="border border-base-500 bg-base-200 p-2 text-sm placeholder:text-base-subtle dark:border-dark-base-200 dark:bg-dark-base-200 dark:placeholder:text-dark-base-subtle"
					/>
					<button
						type="button"
						onclick={submitVoucherNumber}
						disabled={submitting != null || isAccounted || voucherNumber.trim() === ''}
						class="flex min-w-24 cursor-pointer justify-center bg-money-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-money-green-500 disabled:cursor-not-allowed disabled:opacity-50"
					>
						{#if submitting === 'number'}
							<CashSpinner class="size-5" />
						{:else}
							{$_('submit')}
						{/if}
					</button>
				</div>
			</div>
		</div>

		<div class="flex flex-col gap-8 lg:w-2/5 lg:pt-1">
			<div>
				<h2 class="text-base font-semibold">Information</h2>
				<dl class="mt-3 grid grid-cols-[auto_1fr] gap-x-8 gap-y-2 text-sm">
					<dt class="text-base-subtle dark:text-dark-base-subtle">
						{$_('new_expense.form.description.label')}
					</dt>
					<dd>{invoice.description}</dd>

					<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_owner')}</dt>
					<dd>
						{invoice.owner.first_name}
						{invoice.owner.last_name}
						<span class="text-base-subtle dark:text-dark-base-subtle">({invoice.owner.email})</span>
					</dd>

					{#if invoice.invoice_date}
						<dt class="text-base-subtle dark:text-dark-base-subtle">
							{$_('admin_invoices.columns.invoice_date')}
						</dt>
						<dd>{new Date(invoice.invoice_date).toLocaleDateString($locale ?? 'sv-SE')}</dd>
					{/if}

					{#if invoice.due_date}
						<dt class="text-base-subtle dark:text-dark-base-subtle">
							{$_('admin_invoices.columns.due_date')}
						</dt>
						<dd>{new Date(invoice.due_date).toLocaleDateString($locale ?? 'sv-SE')}</dd>
					{/if}

					<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_created_at')}</dt>
					<dd>{new Date(invoice.created_date).toLocaleDateString($locale ?? 'sv-SE')}</dd>
				</dl>
			</div>

			<div>
				<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
				<PartsTable parts={invoice.parts} owner={invoice.owner} partType="invoice" dense />
			</div>
		</div>
	</div>

	<div class="border-t border-base-400 pt-6 dark:border-dark-base-200">
		<h2 class="mb-3 text-base font-semibold">{$_('expense_comments')}</h2>
		<CommentDisplay
			variant="compact"
			comments={invoice.comments}
			currentUser={data.user ?? undefined}
		/>
	</div>
</div>
