<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import type { Expense } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import UserLink from '$lib/components/UserLink.svelte';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';

	let { data }: PageProps = $props();

	let loading = $state(false);

	const columns: TableColumn<Expense>[] = $derived([
		{
			id: 'description',
			header: $_('admin_expenses.columns.description'),
			render: (e) => e.description,
			width: ''
		},
		{
			id: 'owner',
			header: $_('admin_expenses.columns.owner'),
			renderSnippet: ownerCell,
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
			render: (e) => e.created_date,
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

{#snippet ownerCell(e: Expense)}
	<UserLink user={e.owner} />
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

<ClaimFilterBar
	costCentreItems={['Sektionslokalsgruppen']}
	secondaryCostCentreItems={['Allmänt', 'X-scapomiddag']}
	budgetLineItems={['METAdryck', 'Inköp mat']}
	includeChecks={false}
/>

<PaginatedTable
	paginatedResponse={data.expenses}
	columns={[
		{ id: 'id', header: $_('admin_expenses.columns.id'), renderSnippet: idCell, width: 'w-16' },
		...columns
	]}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{loading}
	scrollable
	rowProps={{
		onClick: (e) => goto(`/admin/account/expenses/${e.id}`),
		class: 'cursor-pointer'
	}}
/>
