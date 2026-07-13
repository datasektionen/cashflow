<script lang="ts">
	import { _, locale } from 'svelte-i18n';
	import { ExternalLink } from '@lucide/svelte';
	import type { Invoice } from '$lib/api/types.ts';
	import ReceiptViewer from '$lib/components/ReceiptViewer.svelte';
	import CommentDisplay from '$lib/components/CommentDisplay.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import UserLink from '$lib/components/UserLink.svelte';
	import { api } from '$lib/api';
	import { invalidateAll } from '$app/navigation';
	import { logger } from '$lib/logger';
	import { alerts, error, success } from '$lib/stores/alerts.ts';
	import { isErrorResponse } from '$lib/api/errors.ts';

	let { invoiceId, onPaid }: { invoiceId: number; onPaid?: () => void } = $props();

	let invoicePromise = $derived(api.invoices.get(invoiceId));

	let paying = $state(false);

	async function handlePay(invoice: Invoice) {
		paying = true;
		try {
			await api.invoices.pay(invoice.id);
			alerts.update((a) => [...a, success($_('alerts.invoice_paid'))]);
			await invalidateAll();
			onPaid?.();
		} catch (e) {
			logger.error(e);
			const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
			alerts.update((a) => [...a, error(msg)]);
		} finally {
			paying = false;
		}
	}
</script>

{#await invoicePromise}
	<div class="flex justify-center py-24"><CashSpinner /></div>
{:then invoice}
	<div class="flex flex-col gap-6">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<div class="flex items-center gap-2 text-sm text-base-subtle dark:text-dark-base-subtle">
				<span>{$_('invoice')} #{invoice.id}</span>
				<span>·</span>
				<span><UserLink user={invoice.owner} /></span>
			</div>
			<div class="flex items-center gap-2">
				<a
					href="/admin/invoices/{invoice.id}"
					class="flex cursor-pointer items-center gap-2 border border-base-500 px-3 py-1.5 text-xs font-medium text-base-subtle transition-colors hover:text-base-text dark:border-dark-base-300 dark:text-dark-base-subtle dark:hover:text-dark-base-text"
				>
					{$_('admin_pay.preview.open_detail')}
					<ExternalLink class="size-3.5" />
				</a>
				<button
					onclick={() => handlePay(invoice)}
					disabled={paying}
					class="flex cursor-pointer items-center gap-1.5 bg-money-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-money-green-500 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-money-green-700 dark:hover:bg-money-green-600"
				>
					{#if paying}
						<CashSpinner />
					{:else}
						{$_('invoice_pay')}
					{/if}
				</button>
			</div>
		</div>

		<div class="flex max-h-128 flex-col border">
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

		<dl class="grid grid-cols-[auto_1fr] gap-x-12 gap-y-3 text-sm">
			<dt class="text-base-subtle dark:text-dark-base-subtle">
				{$_('admin_pay.columns.due_date')}
			</dt>
			<dd>
				{invoice.due_date ? new Date(invoice.due_date).toLocaleDateString($locale ?? 'sv-SE') : '–'}
			</dd>
		</dl>

		<div>
			<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
			<PartsTable parts={invoice.parts} owner={invoice.owner} />
		</div>

		<div>
			<h2 class="text-base font-semibold">{$_('expense_comments')}</h2>
			<CommentDisplay comments={invoice.comments} />
		</div>
	</div>
{:catch}
	<div class="py-24 text-center text-sm text-red-500">{$_('action_failed')}</div>
{/await}
