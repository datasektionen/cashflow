<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { Invoice } from '$lib/api/types';
	import type { TableColumn, TableRowProps } from '$lib/components/types';
	import { _ } from 'svelte-i18n';

	let { data }: PageProps = $props();

	let invoices = $derived(data.invoices);

	let loading = $state(false);

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

	const rowProps: TableRowProps<Invoice> = {
		onClick: (invoice) => goto(`/${data.user}/invoices/${invoice.id}`),
		class: 'cursor-pointer'
	};

	const columns: TableColumn<Invoice>[] = $derived([
		{
			key: 'id',
			header: $_('admin_invoices.columns.id'),
			render: (r) => r.id.toString(),
			width: 'w-16'
		},
		{
			key: 'description',
			header: $_('admin_invoices.columns.description'),
			render: (r) => r.description,
			width: 'w-auto'
		},
		{
			key: 'owner',
			header: $_('admin_invoices.columns.owner'),
			render: (r) => r.owner.first_name + ' ' + r.owner.last_name,
			width: 'w-48'
		},
		{
			key: 'invoice_date',
			header: $_('admin_invoices.columns.invoice_date'),
			render: (r) => r.invoice_date,
			width: 'w-32'
		},
		{
			key: 'due_date',
			header: $_('admin_invoices.columns.due_date'),
			render: (r) => r.due_date,
			width: 'w-32'
		},
		{
			key: 'verification',
			header: $_('admin_invoices.columns.verification'),
			render: (r) => r.verification ?? '—',
			width: 'w-32'
		},
		{
			key: 'confirmed_at',
			header: $_('admin_invoices.columns.confirmed_at'),
			render: (r) => r.confirmed_at ?? '—',
			width: 'w-32'
		},
		{
			key: 'paid_at',
			header: $_('admin_invoices.columns.paid_at'),
			render: (r) => r.paid_at ?? '—',
			width: 'w-32'
		}
	]);
</script>

<PaginatedTable
	paginatedResponse={invoices}
	{columns}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{loading}
	{rowProps}
/>
