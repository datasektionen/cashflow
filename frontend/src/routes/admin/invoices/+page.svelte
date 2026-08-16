<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { Invoice } from '$lib/api/types';
	import type { TableColumn } from '$lib/components/types';
	import { _ } from 'svelte-i18n';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';
	import UserLink from '$lib/components/UserLink.svelte';
	import InvoiceStatusPills from '$lib/components/InvoiceStatusPills.svelte';
	import { isExtraSmallLayout, isSmallLayout, isMediumLayout } from '$lib/stores/state.svelte';

	let { data }: PageProps = $props();

	let loading = $state(false);
	let sorting = $state(page.url.searchParams.get('sorting'));

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});

	const columns: TableColumn<Invoice>[] = $derived([
		{
			id: 'description',
			header: $_('admin_invoices.columns.description'),
			render: (r) => r.description,
			width: 'w-48 lg:w-auto'
		},
		{
			id: 'owner',
			header: $_('admin_invoices.columns.owner'),
			renderSnippet: ownerCell,
			width: ''
		},
		{
			id: 'cost_centres',
			header: $_('admin_expenses.columns.cost_centres'),
			renderSnippet: costCentres,
			width: ''
		},
		{
			id: 'invoice_date',
			header: $_('admin_invoices.columns.invoice_date'),
			render: (r) => r.invoice_date,
			width: 'w-28',
			sorting: ['-date', 'date']
		},
		{
			id: 'due_date',
			header: $_('admin_invoices.columns.due_date'),
			render: (r) => r.due_date,
			width: 'w-28'
		},
		{
			id: 'total',
			header: $_('admin_invoices.columns.total'),
			renderSnippet: totalCell,
			width: 'w-32',
			sorting: ['-total', 'total']
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

	function handleSortChange(sort: string) {
		loading = true;
		const url = new URL(page.url);
		if (sort) {
			url.searchParams.set('sorting', sort);
		} else {
			url.searchParams.delete('sorting');
		}
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

{#snippet ownerCell(r: Invoice)}
	<UserLink user={r.owner} class="relative z-10" />
{/snippet}

{#snippet idCell(r: Invoice)}
	<div class="flex flex-row items-center">
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">#</span>
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{r.id}</span>
	</div>
{/snippet}

{#snippet statusCell(r: Invoice)}
	<InvoiceStatusPills invoice={r} />
{/snippet}

{#snippet totalCell(r: Invoice)}
	<span class="tabular-nums">{fmt.format(parseFloat(r.total))} kr</span>
{/snippet}

<ClaimFilterBar exclude={['confirmed', 'flagged', 'voucher_series', 'voucher_number']} />
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
	].filter((col) => {
		if (isExtraSmallLayout.current) return ['description', 'owner'].includes(col.id);
		if (isSmallLayout.current) return ['description', 'owner', 'confirmed_at'].includes(col.id);
		if (isMediumLayout.current)
			return ['description', 'owner', 'invoice_date', 'confirmed_at'].includes(col.id);
		return true;
	})}
	bind:sorting
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	onSortChange={handleSortChange}
	{loading}
	scrollable
	rowProps={{
		href: (r) => `/admin/invoices/${r.id}`,
		class: 'cursor-pointer'
	}}
/>
