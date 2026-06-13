<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import type { Claim } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';

	let { data }: PageProps = $props();

	let loading = $state(false);

	const columns: TableColumn<Claim>[] = $derived([
		{
			key: 'type',
			header: $_('admin_attestable.columns.type'),
			render: (c) => $_(c.type),
			width: 'w-24'
		},
		{
			key: 'description',
			header: $_('admin_attestable.columns.description'),
			render: (c) => c.description,
			width: 'w-auto'
		},
		{
			key: 'owner',
			header: $_('admin_attestable.columns.owner'),
			render: (c) => `${c.owner.first_name} ${c.owner.last_name}`,
			width: 'w-48'
		},
		{
			key: 'created_date',
			header: $_('expense_created_at'),
			render: (c) => c.created_date,
			width: 'w-32'
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

<PaginatedTable
	paginatedResponse={data.claims}
	columns={[
		{ key: 'id', header: $_('admin_attestable.columns.id'), renderSnippet: idCell, width: 'w-16' },
		...columns,
		{
			key: 'is_attested',
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
		onClick: (c) =>
			goto(`/${c.owner.username}/${c.type === 'expense' ? 'expenses' : 'invoices'}/${c.id}`),
		class: 'cursor-pointer'
	}}
/>
