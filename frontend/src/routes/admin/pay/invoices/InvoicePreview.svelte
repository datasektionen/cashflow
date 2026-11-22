<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Button, Spinner } from '#lib/components/ui/index.ts';
	import ClaimPreview from '#lib/components/claim/ClaimPreview.svelte';
	import { api } from '#lib/api/index.ts';
	import { failed, success } from '#lib/stores/alerts.ts';
	import { paidInvoices } from '../expenses/completedPayments.svelte';

	let { invoiceId, canPay = false }: { invoiceId: number; canPay?: boolean } = $props();

	let invoice = $derived(api.invoices.get(invoiceId));
	let paying = $state(false);

	async function handlePay() {
		paying = true;
		try {
			await api.invoices.pay(invoiceId);
			success($_('alerts.invoice_paid'));
			paidInvoices.add(invoiceId);
			invoice = api.invoices.get(invoiceId);
		} catch (e) {
			failed(e, $_('action_failed'));
		} finally {
			paying = false;
		}
	}
</script>

<ClaimPreview claim={invoice} href="/admin/invoices/{invoiceId}">
	{#snippet actions()}
		{#if !paidInvoices.has(invoiceId)}
			<Button onclick={handlePay} disabled={paying || !canPay}>
				{#if paying}<Spinner />{/if}
				{$_('invoice_pay')}
			</Button>
		{/if}
	{/snippet}
</ClaimPreview>
