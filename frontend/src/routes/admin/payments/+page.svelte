<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '#lib/components/PaginatedTable.svelte';
	import type { Payment } from '#lib/api/types.ts';
	import { _ } from 'svelte-i18n';
	import UserCell from '#lib/components/UserCell.svelte';
	import { formatDineroAmount } from '#lib/money.ts';
	import ClaimFilterBar from '#lib/components/ClaimFilterBar.svelte';
	import { byLayout } from '#lib/stores/state.svelte.ts';
	import PaymentRow from './PaymentRow.svelte';

	let { data }: PageProps = $props();

	const columns = $derived(
		byLayout<Payment>(
			[
				{
					id: 'tag',
					header: $_('admin_expenses.columns.tag'),
					renderSnippet: tagCell,
					width: 'w-28'
				},
				{
					id: 'payer',
					header: $_('admin_expenses.columns.payer'),
					renderSnippet: payerCell
				},
				{
					id: 'receiver',
					header: $_('admin_expenses.columns.receiver'),
					renderSnippet: receiverCell,
					width: 'w-48'
				},
				{
					id: 'total',
					header: $_('admin_expenses.columns.total'),
					renderSnippet: totalCell,
					width: 'w-48',
					align: 'right'
				},
				{
					id: 'date',
					header: $_('date'),
					render: (payment) => payment.date,
					width: 'w-32'
				}
			],
			{ xs: ['tag', 'receiver'], sm: ['tag', 'receiver', 'total'] }
		)
	);
</script>

{#snippet expanded(payment: Payment)}
	<PaymentRow {payment} />
{/snippet}

{#snippet tagCell(p: Payment)}
	<span class="font-mono text-xs">{p.tag}</span>
{/snippet}

{#snippet payerCell(p: Payment)}
	<UserCell user={p.payer} />
{/snippet}

{#snippet receiverCell(p: Payment)}
	<UserCell user={p.receiver} />
{/snippet}

{#snippet totalCell(p: Payment)}
	<span class="tabular-nums">{formatDineroAmount(p.total)}</span>
{/snippet}

<ClaimFilterBar
	includeBudget={false}
	includeChecks={false}
	exclude={['verification', 'voucher_series', 'description', 'invoice_number']}
/>
<PaginatedTable
	paginatedResponse={data.payments}
	{columns}
	rowProps={{ expandedSnippet: expanded }}
/>
