<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import type { Claim } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import UserLink from '$lib/components/UserLink.svelte';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';

	let { data }: PageProps = $props();

	let loading = $state(false);

	const columns: TableColumn<Claim>[] = $derived([
		{
			id: 'voucher',
			header: $_('admin_expenses.columns.voucher'),
			renderSnippet: voucherCell,
			width: 'w-28'
		},
		{
			id: 'type',
			header: $_('claims_type'),
			render: (c) => $_(c.type),
			width: 'w-24'
		},
		{
			id: 'description',
			header: $_('admin_expenses.columns.description'),
			render: (c) => c.description,
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
			id: 'amount',
			header: $_('amount'),
			renderSnippet: amountCell,
			width: 'w-32'
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

{#snippet voucherCell(c: Claim)}
	<span class="font-mono text-xs">{c.voucher}</span>
{/snippet}

{#snippet ownerCell(c: Claim)}
	<UserLink user={c.owner} />
{/snippet}

{#snippet costCentres(c: Claim)}
	{@const unique = [...new Set(c.parts.map((p) => p.cost_centre))]}
	<div class="flex flex-wrap gap-1">
		{#each unique as cc}
			<span class="rounded bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
		{/each}
	</div>
{/snippet}

{#snippet amountCell(c: Claim)}
	<span class="tabular-nums">
		{Number(c.amount).toLocaleString('sv-SE', {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		})} kr
	</span>
{/snippet}

<svelte:head>
	<title>{$_('admin_vouchers.title')}</title>
</svelte:head>

<h1 class="mb-4 text-xl font-bold dark:text-slate-100">{$_('admin_vouchers.title')}</h1>

<ClaimFilterBar includeChecks={false} />

<PaginatedTable
	paginatedResponse={data.claims}
	{columns}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{loading}
	scrollable
	rowProps={{
		onClick: (c) => goto(`/admin/${c.type === 'expense' ? 'expenses' : 'invoices'}/${c.id}`),
		class: 'cursor-pointer'
	}}
/>
