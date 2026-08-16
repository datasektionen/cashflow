<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import type { Expense } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';
	import UserLink from '$lib/components/UserLink.svelte';
	import ExpenseStatusPills from '$lib/components/ExpenseStatusPills.svelte';
	import { isExtraSmallLayout, isSmallLayout } from '$lib/stores/state.svelte';

	let { data }: PageProps = $props();

	let loading = $state(false);
	let sorting = $state(page.url.searchParams.get('sorting'));

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});

	const columns: TableColumn<Expense>[] = $derived([
		{
			id: 'description',
			header: $_('admin_expenses.columns.description'),
			render: (e) => e.description,
			width: 'min-w-48'
		},
		{
			id: 'owner',
			header: $_('admin_expenses.columns.owner'),
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
			id: 'expense_date',
			header: $_('expense_date'),
			render: (e) => e.expense_date,
			width: 'w-28',
			sorting: ['-date', 'date']
		},
		{
			id: 'total',
			header: $_('admin_expenses.columns.total'),
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

{#snippet statusCell(e: Expense)}
	<ExpenseStatusPills expense={e} />
{/snippet}

{#snippet ownerCell(e: Expense)}
	<UserLink user={e.owner} class="relative z-10 block truncate" />
{/snippet}

{#snippet idCell(e: Expense)}
	<div class="flex flex-row items-center">
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">#</span>
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{e.id}</span>
	</div>
{/snippet}

{#snippet costCentres(e: Expense)}
	{@const unique = [...new Set(e.parts.map((p) => p.cost_centre))]}
	<div class="flex flex-wrap gap-1">
		{#each unique as cc}
			<span class="rounded bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
		{/each}
	</div>
{/snippet}

{#snippet totalCell(e: Expense)}
	<span class="tabular-nums">{fmt.format(parseFloat(e.total))} kr</span>
{/snippet}
<ClaimFilterBar exclude={['voucher_series', 'voucher_number']} />

<PaginatedTable
	paginatedResponse={data.expenses}
	columns={[
		{ id: 'id', header: $_('admin_expenses.columns.id'), renderSnippet: idCell, width: 'w-16' },
		...columns,
		{
			id: 'confirmed_at',
			header: $_('admin_expenses.columns.status'),
			renderSnippet: statusCell,
			width: 'w-56'
		}
	].filter((col) => {
		// Extra small is a subset of small, so check it first: show only the
		// essentials, dropping cost centres on top of the small-screen hides.
		if (isExtraSmallLayout.current) return ['description', 'owner'].includes(col.id);
		if (isSmallLayout.current)
			return !['id', 'expense_date', 'total', 'confirmed_at'].includes(col.id);
		return true;
	})}
	bind:sorting
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	onSortChange={handleSortChange}
	{loading}
	scrollable
	rowProps={{
		href: (e) => `/admin/expenses/${e.id}`,
		class: 'cursor-pointer'
	}}
/>
