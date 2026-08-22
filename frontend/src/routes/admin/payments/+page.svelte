<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import type { Payment } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import UserLink from '$lib/components/UserLink.svelte';
	import { formatAmount } from '$lib/money';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';
	import { isExtraSmallLayout, isSmallLayout } from '$lib/stores/state.svelte';
	import PaymentRow from './PaymentRow.svelte';

	let { data }: PageProps = $props();

	let loading = $state(false);

	const columns: TableColumn<Payment>[] = $derived(
		(
			[
				{
					id: 'tag',
					header: $_('admin_expenses.columns.tag'),
					render: (payment) => payment.tag,
					width: 'w-28'
				},
				{
					id: 'payer',
					header: $_('admin_expenses.columns.payer'),
					renderSnippet: payerCell,
					width: ''
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
					render: (p) => formatAmount(p.total),
					width: 'w-48'
				},
				{
					id: 'date',
					header: $_('expense_created_at'),
					render: (payment) => payment.date,
					width: 'w-28'
				}
			] as TableColumn<Payment>[]
		).filter((col) => {
			if (isExtraSmallLayout.current) return ['tag', 'receiver'].includes(col.id);
			if (isSmallLayout.current) return ['tag', 'receiver', 'total'].includes(col.id);
			return true;
		})
	);

	function handlePageChange(p: number) {
		loading = true;
		const url = new URL(page.url);
		url.searchParams.set('page', p.toString());
		goto(url, { keepFocus: true, noScroll: true, replaceState: true }).then(
			() => (loading = false)
		);
	}

	function handlePerPageChange(perPage: number) {
		loading = true;
		const url = new URL(page.url);
		url.searchParams.set('per_page', perPage.toString());
		url.searchParams.set('page', '1');
		goto(url, { keepFocus: true, noScroll: true, replaceState: true }).then(
			() => (loading = false)
		);
	}
</script>

{#snippet expanded(payment: Payment)}
	<PaymentRow {payment} />
{/snippet}

{#snippet payerCell(p: Payment)}
	<UserLink user={p.payer} class="relative z-10" />
{/snippet}

{#snippet receiverCell(p: Payment)}
	<UserLink user={p.receiver} class="relative z-10" />
{/snippet}

<ClaimFilterBar
	includeBudget={false}
	includeChecks={false}
	exclude={['voucher_number', 'voucher_series', 'description']}
/>
<PaginatedTable
	paginatedResponse={data.payments}
	{columns}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{loading}
	scrollable
	rowProps={{
		class: 'cursor-pointer',
		expandedSnippet: expanded
	}}
/>
