<script lang="ts">
	import { latest } from '#lib/latest.svelte.ts';
	import { formatDate } from '#lib/date.ts';
	import type { PageProps } from './$types';
	import type { Invoice } from '#lib/api/types.ts';
	import { DUE_WARNING_DAYS } from '#lib/config.ts';
	import PaginatedTable from '#lib/components/PaginatedTable.svelte';
	import { Check, CircleCheck, Clock, TriangleAlert } from '@lucide/svelte';
	import { goto } from '$app/navigation';
	import { _ } from 'svelte-i18n';
	import UserLink from '#lib/components/UserLink.svelte';
	import InvoicePreview from './InvoicePreview.svelte';
	import { mayPay } from '#lib/auth.ts';
	import { paidInvoices } from '../expenses/completedPayments.svelte';
	import { byLayout, isMediumLayout } from '#lib/stores/state.svelte.ts';
	import { formatDineroAmount, claimTotal } from '#lib/money.ts';
	import { EmptyState } from '#lib/components/ui/index.ts';

	let { data }: PageProps = $props();
	const canPay = $derived(mayPay(data.user));

	const list = latest(() => data.invoices);
	const empty = $derived(list.value?.pagination.total === 0);

	let preview: Invoice | null = $state(null);

	function handleRowClick(invoice: Invoice) {
		if (isMediumLayout.current) goto(`/admin/invoices/${invoice.id}`);
		else preview = invoice;
	}

	const columns = $derived(
		byLayout<Invoice>(
			[
				{
					id: 'invoice',
					header: $_('admin_pay.columns.invoice'),
					renderSnippet: invoiceCell,
					sorting: ['-description', 'description']
				},
				{
					id: 'due_date',
					header: $_('admin_pay.columns.due_date'),
					renderSnippet: dueDateCell,
					width: 'w-32',
					sorting: ['due_date', '-due_date']
				},
				{
					id: 'total',
					header: $_('admin_pay.columns.total'),
					renderSnippet: totalCell,
					width: 'w-32',
					align: 'right',
					sorting: ['-total', 'total']
				}
			],
			{ sm: ['invoice', 'total'] }
		)
	);
</script>

{#snippet invoiceCell(invoice: Invoice)}
	{@const paid = paidInvoices.has(invoice.id)}
	<div class="flex min-w-0 flex-col gap-1">
		<span class="flex min-w-0 items-center gap-1.5 font-medium">
			<span class={['min-w-0 truncate', paid && 'opacity-50']}>{invoice.description}</span>
			{#if paid}
				<Check class="size-4 shrink-0 text-primary" />
			{/if}
		</span>
		<span class="flex items-center gap-3 text-xs text-muted-foreground">
			<span class={[paid && 'opacity-50']}><UserLink user={invoice.owner} /></span>
			{#if paid}
				<span class="font-mono">CF {invoice.id}</span>
			{/if}
		</span>
	</div>
{/snippet}

{#snippet dueDateCell(invoice: Invoice)}
	{@const dueDate = invoice.due_date ? new Date(invoice.due_date) : null}
	{@const dueSoon = dueDate ? dueDate.getTime() - DUE_WARNING_DAYS * 86400000 < Date.now() : false}
	{@const pastDue = dueDate ? dueDate.getTime() < Date.now() : false}
	<span
		class={[
			'flex items-center gap-1 tabular-nums',
			pastDue && 'text-danger',
			dueSoon && !pastDue && 'text-warning',
			paidInvoices.has(invoice.id) && 'opacity-50'
		]}
	>
		{#if pastDue}
			<TriangleAlert class="size-4 shrink-0" />
		{:else if dueSoon}
			<Clock class="size-4 shrink-0" />
		{/if}
		{dueDate ? formatDate(dueDate) : '–'}
	</span>
{/snippet}

{#snippet totalCell(invoice: Invoice)}
	<span class={['font-medium tabular-nums', paidInvoices.has(invoice.id) && 'opacity-50']}>
		{formatDineroAmount(claimTotal(invoice))} kr
	</span>
{/snippet}

{#if empty}
	<EmptyState icon={CircleCheck} title={$_('admin_pay.empty')} class="max-w-4xl" />
{:else}
	<!-- viewport minus navbar, main padding, page title and tabs -->
	<div class="flex flex-col gap-6 lg:h-[calc(100dvh-14rem)] lg:flex-row lg:overflow-hidden">
		<div class="min-w-0 lg:min-h-0 lg:flex-[3] lg:overflow-y-auto">
			<PaginatedTable
				paginatedResponse={data.invoices}
				{columns}
				scrollable
				rowProps={{
					onClick: handleRowClick,
					class: (invoice: Invoice) => (preview?.id === invoice.id ? 'bg-muted' : '')
				}}
			/>
		</div>

		<div class="hidden min-h-0 lg:flex lg:flex-[2]">
			{#if preview}
				{#key preview.id}
					<InvoicePreview invoiceId={preview.id} {canPay} />
				{/key}
			{:else}
				<EmptyState title={$_('admin_pay.preview.empty')} class="w-full" />
			{/if}
		</div>
	</div>
{/if}
