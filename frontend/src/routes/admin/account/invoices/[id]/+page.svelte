<script lang="ts">
	import { _, locale } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import { ChevronDown } from '@lucide/svelte';
	import type { PageData } from './$types';
	import { api } from '$lib/api';
	import { mayAccount } from '$lib/auth';
	import { isErrorResponse } from '$lib/api/errors';
	import { alerts, error, success } from '$lib/stores/alerts';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import CommentDisplay from '$lib/components/CommentDisplay.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import ReceiptViewer from '$lib/components/ReceiptViewer.svelte';
	import UserLink from '$lib/components/UserLink.svelte';
	import VoucherRowFields, { draftsFromParts, toVoucherRows } from '../../VoucherRowFields.svelte';
	import type { VoucherRowDraft } from '../../VoucherRowFields.svelte';
	import { sumAmounts } from '$lib/money';
	import CopyableValue from '$lib/components/ui/CopyableValue.svelte';
	import { formatAmount } from '$lib/money';

	let { data }: { data: PageData } = $props();
	const invoice = $derived(data.invoice);
	const expectedTotal = $derived(sumAmounts(invoice.parts.map((p) => p.amount)));
	let voucherRowFields: VoucherRowFields | undefined = $state();
	// Receipt preview is collapsible to keep the accounting column uncluttered;
	// open by default so accountants can eyeball amounts against the receipt.
	let showReceipt = $state(true);

	// Prefill once; the form must not reset if data refreshes while editing.
	// svelte-ignore state_referenced_locally
	const drafts = draftsFromParts(data.invoice.parts, data.invoice.recommended_credit_account);
	// The last draft is the balancing credit row; it can't be deleted, and its
	// cost centre and amount stay locked, but the account remains editable.
	// svelte-ignore state_referenced_locally
	if (data.invoice.parts.length > 0) {
		const balancing = drafts[drafts.length - 1];
		balancing.lockedFields = ['cost_centre', 'debit', 'credit'];
		balancing.deletable = false;
	}
	let voucherRows = $state<VoucherRowDraft[]>(drafts);
	let voucherNumber = $state('');
	// Which of the two submit buttons is in flight, so only it shows a spinner.
	let submitting = $state<'rows' | 'number' | null>(null);

	const isAccounted = $derived(invoice.voucher != null);

	async function submitAccounting(
		kind: 'rows' | 'number',
		payload: Parameters<typeof api.invoices.account>[1]
	) {
		submitting = kind;
		try {
			const updated = await api.invoices.account(invoice.id, payload);
			alerts.update((a) => [
				...a,
				success($_('admin_account.success', { values: { verification: updated.voucher } }))
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
		if (!voucherRowFields?.validate()) return;
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
		{#if invoice.voucher}
			<span
				class="bg-money-green-900 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-200 dark:text-money-green-900"
				>{invoice.voucher}</span
			>
		{/if}
	</div>
</div>

<div class="flex flex-wrap gap-8">
	<div class="flex min-w-0 grow basis-[51rem] flex-col gap-8 pt-1">
		<div>
			<h2 class="mb-2 text-base font-semibold">{$_('admin_account.create_voucher')}</h2>
			<p
				class="hidden max-w-prose pb-4 text-xs leading-relaxed text-base-subtle md:flex dark:text-dark-base-subtle"
			>
				{$_('admin_account.create_voucher_help')}
			</p>
			<VoucherRowFields
				bind:this={voucherRowFields}
				bind:voucherRows
				accounts={data.accounts}
				costCentres={data.costCentres}
				{expectedTotal}
			/>
			<div class="mt-4 flex justify-end">
				<button
					type="button"
					onclick={submitVoucherRows}
					disabled={submitting != null ||
						isAccounted ||
						!hasSubmittableRows ||
						!mayAccount(data.user)}
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
			<h2 class="mb-2 text-base font-semibold">{$_('admin_account.manual_accounting')}</h2>

			<div class="flex flex-col justify-between md:flex-row">
				<div class="my-2 flex flex-col gap-y-2">
					<CopyableValue
						class="h-12 md:h-8"
						value="CF {invoice.id} {invoice.description}"
						display="CF {invoice.id} {invoice.description}"
					/>

					<CopyableValue
						class="h-12 md:h-8"
						value={invoice.invoice_date}
						display={invoice.invoice_date}
					/>

					<CopyableValue
						class="h-12 md:h-8"
						value={formatAmount(invoice.total)}
						display="{invoice.total} kr"
					/>
				</div>

				<div class="flex flex-col">
					<p
						class="hidden max-w-prose pb-4 text-xs leading-relaxed text-base-subtle md:flex dark:text-dark-base-subtle"
					>
						{$_('admin_account.existing_voucher_help')}
					</p>
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
							disabled={submitting != null ||
								isAccounted ||
								voucherNumber.trim() === '' ||
								!mayAccount(data.user)}
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

	<div class="flex min-w-0 grow basis-80 flex-col gap-8 pt-1">
		<div>
			<h2 class="text-base font-semibold">Information</h2>
			<dl class="mt-3 grid grid-cols-[auto_minmax(0,1fr)] gap-x-8 gap-y-2 text-sm break-words">
				<dt class="text-base-subtle dark:text-dark-base-subtle">
					{$_('new_expense.form.description.label')}
				</dt>
				<dd>{invoice.description}</dd>

				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_owner')}</dt>
				<dd>
					<UserLink user={invoice.owner} />
					<span class="text-base-subtle dark:text-dark-base-subtle">({invoice.owner.email})</span>
				</dd>

				{#if invoice.invoice_date}
					<dt class="text-base-subtle dark:text-dark-base-subtle">
						{$_('admin_invoices.columns.invoice_date')}
					</dt>
					<dd>{new Date(invoice.invoice_date).toLocaleDateString($locale ?? 'sv-SE')}</dd>
				{/if}
			</dl>
		</div>

		<div>
			<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
			<PartsTable parts={invoice.parts} owner={invoice.owner} partType="invoice" dense />
		</div>

		<div>
			<button
				type="button"
				onclick={() => (showReceipt = !showReceipt)}
				class="flex w-full cursor-pointer items-center gap-1.5 text-base font-semibold"
				aria-expanded={showReceipt}
			>
				<ChevronDown class="size-4 transition-transform {showReceipt ? '' : '-rotate-90'}" />
				{$_('expense_receipt')}
			</button>
			{#if showReceipt}
				<div class="mt-3 flex h-160 flex-col">
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
			{/if}
		</div>
	</div>
</div>
