<script lang="ts">
	import { _ } from 'svelte-i18n';
	import type { Invoice } from '$lib/api/types';
	import StatusPill from '$lib/components/StatusPill.svelte';

	let { invoice }: { invoice: Invoice } = $props();

	const isAttested = $derived(
		invoice.parts.length > 0 && invoice.parts.every((p) => p.attested_by != null)
	);
	const done = $derived(invoice.paid_at || invoice.voucher);
</script>

<div class="flex gap-3">
	{#if !done && isAttested}
		<StatusPill tone="attested" label={$_('expense_attested')} />
	{/if}
	{#if invoice.paid_at}
		<StatusPill tone="paid" label={$_('expense_paid')} />
	{/if}
	{#if invoice.voucher}
		<StatusPill tone="voucher" label={invoice.voucher} mono />
	{/if}
	{#if !isAttested && !invoice.paid_at && !invoice.voucher}
		<StatusPill tone="neutral" label={$_('expense_status.not_attested')} />
	{/if}
</div>
