<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { formatDate } from '#lib/date.ts';
	import type { Expense, Invoice } from '#lib/api/types.ts';
	import { Card } from '#lib/components/ui/index.ts';
	import UserLink from '#lib/components/UserLink.svelte';
	import InfoItem from './InfoItem.svelte';

	let { claim, linkOwner = false }: { claim: Expense | Invoice; linkOwner?: boolean } = $props();

	const isExpense = $derived('expense_date' in claim);
	const date = $derived('expense_date' in claim ? claim.expense_date : claim.invoice_date);
	const paid = $derived(
		'payment' in claim
			? claim.payment && { by: claim.payment.payer, at: claim.payment.date, tag: claim.payment.tag }
			: claim.paid_at && { by: claim.paid_by, at: claim.paid_at, tag: null }
	);

	const name = (p: { first_name: string; last_name: string } | null | undefined) =>
		p ? `${p.first_name} ${p.last_name}` : '';
	const optionalDate = (d: string | null | undefined) => (d ? formatDate(d) : '–');
</script>

{#snippet pending(text: string)}
	<span class="font-normal text-muted-foreground">{text}</span>
{/snippet}

<Card padded={false} class="divide-y divide-border">
	<dl class="grid grid-cols-2 gap-x-6 gap-y-4 px-5 py-4 sm:auto-cols-fr sm:grid-flow-col">
		<InfoItem label={$_('expense_owner')} sub={claim.owner.email}>
			{#if linkOwner}<UserLink user={claim.owner} />{:else}{name(claim.owner)}{/if}
		</InfoItem>
		<InfoItem label={isExpense ? $_('expense_date') : $_('admin_invoices.columns.invoice_date')}>
			{optionalDate(date)}
		</InfoItem>
		{#if 'due_date' in claim}
			<InfoItem label={$_('admin_invoices.columns.due_date')}>
				{optionalDate(claim.due_date)}
			</InfoItem>
		{/if}
		<InfoItem label={$_('expense_created_at')}>{formatDate(claim.created_date)}</InfoItem>
	</dl>
	<dl class="grid grid-cols-2 gap-x-6 gap-y-4 px-5 py-4 sm:grid-cols-3">
		<InfoItem
			label={$_('expense_confirmed')}
			done={!!claim.confirmed_at}
			sub={claim.confirmed_at && formatDate(claim.confirmed_at)}
		>
			{#if claim.confirmed_at}
				{name(claim.confirmed_by) || '–'}
			{:else}
				{@render pending($_('expense_status.unprocessed'))}
			{/if}
		</InfoItem>
		<InfoItem
			label={isExpense ? $_('expense_paid') : $_('admin_invoices.columns.paid_at')}
			done={!!paid}
			sub={paid && [formatDate(paid.at), paid.tag].filter(Boolean).join(' ')}
		>
			{#if paid}
				{name(paid.by) || '–'}
			{:else}
				{@render pending(isExpense ? $_('expense_status.unpaid') : $_('not_paid'))}
			{/if}
		</InfoItem>
		<InfoItem label={$_('expense_verification')} done={!!claim.voucher}>
			{#if claim.voucher}
				<span class="font-mono">{claim.voucher}</span>
			{:else}
				{@render pending($_('expense_status.not_booked'))}
			{/if}
		</InfoItem>
	</dl>
</Card>
