<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { Invoice } from '$lib/api/types';
	import type { TableColumn } from '$lib/components/types';
	import { _ } from 'svelte-i18n';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';

	let { data }: PageProps = $props();

	let loading = $state(false);

	const columns: TableColumn<Invoice>[] = $derived([
		{
			id: 'description',
			header: $_('admin_invoices.columns.description'),
			render: (r) => r.description,
			width: ''
		},
		{
			id: 'owner',
			header: $_('admin_invoices.columns.owner'),
			render: (r) => r.owner.first_name + ' ' + r.owner.last_name,
			width: 'w-48'
		},
		{
			id: 'cost_centres',
			header: $_('admin_expenses.columns.cost_centres'),
			renderSnippet: costCentres,
			width: 'w-48'
		},
		{
			id: 'created_date',
			header: $_('expense_created_at'),
			render: (r) => r.created_date,
			width: 'w-28'
		},
		{
			id: 'due_date',
			header: $_('admin_invoices.columns.due_date'),
			render: (r) => r.due_date,
			width: 'w-28'
		}
	]);

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

{#snippet costCentres(r: Invoice)}
	{@const unique = [...new Set(r.parts.map((p) => p.cost_centre))]}
	<div class="flex flex-wrap gap-1">
		{#each unique as cc}
			<span class="rounded bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
		{/each}
	</div>
{/snippet}

{#snippet idCell(r: Invoice)}
	<div class="flex flex-row items-center">
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">#</span>
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{r.id}</span>
	</div>
{/snippet}

{#snippet statusCell(r: Invoice)}
	{@const isAttested = r.parts.length > 0 && r.parts.every((p) => p.attested_by != null)}
	{@const done = r.paid_at || r.verification}
	<div class="flex gap-3">
		{#if !done && isAttested}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-400 dark:bg-money-green-500"
				></span>
				{$_('expense_attested')}
			</span>
		{/if}
		{#if !done && r.confirmed_at}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-500 dark:bg-money-green-400"
				></span>
				{$_('expense_confirmed')}
			</span>
		{/if}
		{#if r.paid_at}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-600 dark:bg-money-green-400"
				></span>
				{$_('expense_paid')}
			</span>
		{/if}
		{#if r.verification}
			<span class="flex items-center gap-1.5 font-mono text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-700 dark:bg-money-green-300"
				></span>
				{r.verification}
			</span>
		{/if}
		{#if !isAttested && !r.confirmed_at && !r.paid_at && !r.verification}
			<span class="flex items-center gap-1.5 text-xs text-base-subtle dark:text-dark-base-subtle">
				<span class="inline-block size-1.5 shrink-0 rounded-full bg-base-400 dark:bg-dark-base-400"
				></span>
				{$_('expense_status.unconfirmed')}
			</span>
		{/if}
	</div>
{/snippet}

<ClaimFilterBar
	costCentreItems={['Sektionslokalsgruppen']}
	secondaryCostCentreItems={['Allmänt', 'X-scapomiddag']}
	budgetLineItems={['METAdryck', 'Inköp mat']}
/>
<PaginatedTable
	paginatedResponse={data.invoices}
	columns={[
		{ id: 'id', header: $_('admin_invoices.columns.id'), renderSnippet: idCell, width: 'w-16' },
		...columns,
		{
			id: 'confirmed_at',
			header: $_('admin_invoices.columns.status'),
			renderSnippet: statusCell,
			width: 'w-56'
		}
	]}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{loading}
	scrollable
	rowProps={{
		onClick: (r) => goto(`/${data.user}/invoices/${r.id}`),
		class: 'cursor-pointer'
	}}
/>
