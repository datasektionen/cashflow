<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import type { Claim } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';
	import UserLink from '$lib/components/UserLink.svelte';

	let { data }: PageProps = $props();

	let loading = $state(false);

	const columns: TableColumn<Claim>[] = $derived([
		{
			id: 'type',
			header: $_('admin_attestable.columns.type'),
			render: (c) => $_(c.type),
			width: 'w-24'
		},
		{
			id: 'description',
			header: $_('admin_attestable.columns.description'),
			render: (c) => c.description,
			width: ''
		},
		{
			id: 'owner',
			header: $_('admin_attestable.columns.owner'),
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
			render: (c) => c.created_date,
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

{#snippet costCentres(c: Claim)}
	{@const unique = [...new Set(c.parts.map((p) => p.cost_centre))]}
	<div class="flex flex-wrap gap-1">
		{#each unique as cc}
			<span class="rounded bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
		{/each}
	</div>
{/snippet}

{#snippet ownerCell(c: Claim)}
	<UserLink user={c.owner} />
{/snippet}

{#snippet idCell(c: Claim)}
	<div class="flex flex-row items-center">
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">#</span>
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{c.id}</span>
	</div>
{/snippet}

{#snippet statusCell(c: Claim)}
	<div class="flex gap-3">
		{#if c.is_paid}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-600 dark:bg-money-green-400"
				></span>
				{$_('expense_paid')}
			</span>
		{:else if c.is_confirmed}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-500 dark:bg-money-green-400"
				></span>
				{$_('expense_confirmed')}
			</span>
		{:else if c.is_attested}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-400 dark:bg-money-green-500"
				></span>
				{$_('expense_attested')}
			</span>
		{:else}
			<span class="flex items-center gap-1.5 text-xs text-base-subtle dark:text-dark-base-subtle">
				<span class="inline-block size-1.5 shrink-0 rounded-full bg-base-400 dark:bg-dark-base-400"
				></span>
				{$_('expense_status.unconfirmed')}
			</span>
		{/if}
	</div>
{/snippet}

<ClaimFilterBar exclude={['attested', 'paid', 'accounted', 'flagged', 'voucher_series']} />
<PaginatedTable
	paginatedResponse={data.claims}
	columns={[
		{ id: 'id', header: $_('admin_attestable.columns.id'), renderSnippet: idCell, width: 'w-16' },
		...columns,
		{
			id: 'is_attested',
			header: $_('admin_attestable.columns.status'),
			renderSnippet: statusCell,
			width: 'w-40'
		}
	]}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{loading}
	scrollable
	rowProps={{
		onClick: (c) => goto(`/admin/${c.type === 'expense' ? 'expenses' : 'invoices'}/${c.id}`),
		class: 'cursor-pointer'
	}}
/>
