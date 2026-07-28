<script lang="ts">
	import { _ } from 'svelte-i18n';
	import type { Expense } from '$lib/api/types';
	import StatusPill from '$lib/components/StatusPill.svelte';

	let { expense }: { expense: Expense } = $props();

	const isAttested = $derived(
		expense.parts.length > 0 && expense.parts.every((p) => p.attested_by != null)
	);
	const done = $derived(expense.payment || expense.voucher);
</script>

<div class="flex gap-3">
	{#if expense.is_flagged}
		<StatusPill tone="flagged" label={$_('expense_flagged')} />
	{/if}
	{#if !done && isAttested}
		<StatusPill tone="attested" label={$_('expense_attested')} />
	{/if}
	{#if !done && expense.confirmed_at}
		<StatusPill tone="confirmed" label={$_('expense_confirmed')} />
	{/if}
	{#if expense.payment}
		<StatusPill tone="paid" label={$_('expense_paid')} />
	{/if}
	{#if expense.voucher}
		<StatusPill tone="voucher" label={expense.voucher} mono />
	{/if}
	{#if !isAttested && !expense.confirmed_at && !expense.payment && !expense.voucher && !expense.is_flagged}
		<StatusPill tone="neutral" label={$_('expense_status.unconfirmed')} />
	{/if}
</div>
