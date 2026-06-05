<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import type { Expense } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';

	let { data }: PageProps = $props();

	const columns: TableColumn<Expense>[] = $derived([
		{
			key: 'id',
			header: $_('admin_expenses.columns.id'),
			render: (e) => e.id.toString(),
			width: 'w-16'
		},
		{
			key: 'verification',
			header: $_('admin_expenses.columns.voucher'),
			render: (e) => e.verification,
			width: 'w-32'
		},
		{
			key: 'description',
			header: $_('admin_expenses.columns.description'),
			render: (e) => e.description,
			width: 'w-auto'
		},
		{
			key: 'owner',
			header: $_('admin_expenses.columns.owner'),
			render: (e) => `${e.owner.first_name} ${e.owner.last_name}`,
			width: 'w-56'
		},
		{
			key: 'expense_date',
			header: $_('admin_expenses.columns.expense_date'),
			render: (e) => e.expense_date,
			width: 'w-32'
		}
	]);

	function handlePageChange(p: number) {
		const url = new URL(page.url);
		url.searchParams.set('page', p.toString());
		goto(url, { keepFocus: true, noScroll: true });
	}

	function handlePerPageChange(perPage: number) {
		const url = new URL(page.url);
		url.searchParams.set('per_page', perPage.toString());
		url.searchParams.set('page', '1');
		goto(url, { keepFocus: true, noScroll: true });
	}
</script>

<PaginatedTable
	paginatedResponse={data.expenses}
	{columns}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	rowProps={{
		onClick: (e) => goto(`/${e.owner.username}/expenses/${e.id}`),
		class: 'cursor-pointer'
	}}
/>
