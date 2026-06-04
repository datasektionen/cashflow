<script lang="ts">
    import type { PageProps } from './$types';
    import { goto } from '$app/navigation';
    import { page } from '$app/state';
    import { _ } from 'svelte-i18n';
    import PaginatedTable from '$lib/components/PaginatedTable.svelte';
    import type { TableColumn } from '$lib/components/types';
    import type { Claim } from '$lib/api/types';

    let { data }: PageProps = $props();

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

    const columns: TableColumn<Claim>[] = [
        {
            key: 'type',
            header: $_('claims_type'),
            render: row => $_(row.type),
            width: 'w-24',
        },
        {
            key: 'description',
            header: $_('admin_invoices.columns.description'),
            render: row => row.description,
            width: 'auto',
        },
        {
            key: 'date',
            header: $_('admin_expenses.columns.expense_date'),
            render: row => new Date(row.date).toLocaleDateString(),
            width: 'w-32',
        },
    ];
</script>

<PaginatedTable
    paginatedResponse={data.claims}
    {columns}
    onPageChange={handlePageChange}
    onPerPageChange={handlePerPageChange}
/>
