<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import ClaimFilterBar from '../ClaimFilterBar.svelte';
	import PaginatedTable from '../PaginatedTable.svelte';
	import type { TableColumn } from '../types';
	import {
		type Claim,
		type Expense,
		type Invoice,
		type PaginatedResponse,
		type User
	} from '#lib/api/types.ts';
	import { _ } from 'svelte-i18n';
	import ClaimContextMenu from '../ClaimContextMenu.svelte';
	import UserLink from '../UserLink.svelte';
	import { formatDineroAmount, sumDinero } from '#lib/money.ts';
	import { isExtraSmallLayout, isSmallLayout } from '#lib/stores/state.svelte.ts';
	import ClaimStatusPills from '../ClaimStatusPills.svelte';
	import ExpenseStatusPills from '../ExpenseStatusPills.svelte';
	import InvoiceStatusPills from '../InvoiceStatusPills.svelte';
	import type { Filter } from '../ClaimFilterBar.svelte';

	let loading: boolean = $state(false);
	let sorting = $state(page.url.searchParams.get('sorting'));

	type AnyClaim = Claim | Expense | Invoice;

	const getType = (c: AnyClaim) => {
		if ('type' in c) {
			return c.type;
		}
		if ('invoice_date' in c) {
			return 'invoice';
		} else {
			return 'expense';
		}
	};

	const getAmount = (c: AnyClaim) => {
		if ('amount' in c) {
			return c.amount;
		} else {
			return sumDinero(c.parts.map((p) => p.amount));
		}
	};

	const getDate = (c: AnyClaim) => {
		if ('type' in c) {
			return c.type === 'expense' ? c.expense_date : c.invoice_date;
		} else if ('expense_date' in c) {
			return c.expense_date;
		} else {
			return c.invoice_date;
		}
	};

	type ColumnOption =
		| 'verification'
		| 'id'
		| 'type'
		| 'description'
		| 'owner'
		| 'cost_centres'
		| 'date'
		| 'amount'
		| 'status'
		| '__all__';

	let {
		claims,
		user,
		onRowClick = (c) =>
			goto(`/admin/${getType(c) === 'expense' ? 'expenses' : 'invoices'}/${c.id}`),
		filters,
		includeColumns = ['__all__'],
		excludeColumns = []
	}: {
		claims: Promise<PaginatedResponse<AnyClaim>>;
		user: User;
		onRowClick?: (c: AnyClaim) => void;
		filters: Filter[];
		includeColumns?: ColumnOption[];
		excludeColumns?: ColumnOption[];
	} = $props();

	let columns: TableColumn<AnyClaim>[] = $derived(
		[
			{
				id: 'verification',
				header: $_('admin_expenses.columns.voucher'),
				renderSnippet: voucherCell,
				width: 'w-28'
			},

			{ id: 'id', header: $_('admin_attestable.columns.id'), renderSnippet: idCell, width: 'w-16' },
			{
				id: 'type',
				header: $_('admin_attestable.columns.type'),
				render: (c: AnyClaim) => $_(getType(c)),
				width: 'w-24',
				sorting: ['-type', 'type']
			},
			{
				id: 'description',
				header: $_('admin_attestable.columns.description'),
				render: (c: AnyClaim) => c.description,
				width: 'w-48 truncate'
			},
			{
				id: 'owner',
				header: $_('admin_attestable.columns.owner'),
				renderSnippet: ownerCell,
				width: 'w-24 lg:w-40',
				sorting: ['-user', 'user']
			},
			{
				id: 'cost_centres',
				header: $_('admin_expenses.columns.cost_centres'),
				renderSnippet: costCentres,
				width: 'w-48',
				sorting: ['-cost_centre', 'cost_centre']
			},
			{
				id: 'date',
				header: $_('date'),
				render: (c: AnyClaim) => getDate(c),
				width: 'w-28',
				sorting: ['-date', 'date']
			},
			{
				id: 'amount',
				header: $_('admin_attestable.columns.amount'),
				renderSnippet: amountCell,
				width: 'w-32',
				sorting: ['-total', 'total']
			},
			{
				id: 'status',
				header: $_('admin_attestable.columns.status'),
				renderSnippet: statusCell,
				width: 'w-56'
			}
		]
			.filter((col) => {
				if (isExtraSmallLayout.current) return ['description', 'owner'].includes(col.id);
				if (isSmallLayout.current)
					return !['id', 'expense_date', 'amount', 'is_attested'].includes(col.id);
				return true;
			})
			.filter((col) => {
				return (
					(includeColumns.includes(col.id as ColumnOption) || includeColumns.includes('__all__')) &&
					!excludeColumns.includes(col.id as ColumnOption)
				);
			})
	);

	let excludedFilters: Filter[] = $derived(
		(
			[
				'attested',
				'confirmed',
				'paid',
				'accounted',
				'flagged',
				'voucher_series',
				'reimbursement',
				'description',
				'verification',
				'invoice_number'
			] as Filter[]
		).filter((f) => !filters.includes(f))
	);

	function handlePageChange(p: number) {
		loading = true;
		const url = new URL(page.url.href);
		url.searchParams.set('page', p.toString());
		goto(url, { reset: false, replaceState: true }).then(() => (loading = false));
	}

	function handlePerPageChange(perPage: number) {
		loading = true;
		const url = new URL(page.url.href);
		url.searchParams.set('per_page', perPage.toString());
		url.searchParams.set('page', '1');
		goto(url, { reset: false, replaceState: true }).then(() => (loading = false));
	}

	function handleSortChange(sort: string) {
		loading = true;
		const url = new URL(page.url.href);
		if (sort) {
			url.searchParams.set('sorting', sort);
		} else {
			url.searchParams.delete('sorting');
		}
		goto(url, { reset: false, replaceState: true }).then(() => (loading = false));
	}
</script>

{#snippet contextSnippet(c: AnyClaim)}
	<ClaimContextMenu claim={c} kind={getType(c)} {user} />
{/snippet}

{#snippet costCentres(c: AnyClaim)}
	{@const unique = [...new Set(c.parts.map((p) => p.cost_centre))]}
	<div class="flex flex-wrap gap-1">
		{#each unique as cc}
			<span class="rounded bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
		{/each}
	</div>
{/snippet}

{#snippet voucherCell(c: Claim | Expense | Invoice)}
	<span class="font-mono text-xs">{c.voucher != null ? c.voucher : 'n/a'}</span>
{/snippet}

{#snippet ownerCell(c: AnyClaim)}
	<UserLink user={c.owner} class="block truncate" />
{/snippet}

{#snippet amountCell(c: AnyClaim)}
	<span class="tabular-nums">{formatDineroAmount(getAmount(c))} kr</span>
{/snippet}

{#snippet idCell(c: AnyClaim)}
	<div class="flex flex-row items-center">
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">#</span>
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{c.id}</span>
	</div>
{/snippet}

{#snippet statusCell(c: AnyClaim)}
	{#if 'type' in c}
		<ClaimStatusPills claim={c} />
	{:else if 'expense_date' in c}
		<ExpenseStatusPills expense={c} />
	{:else}
		<InvoiceStatusPills invoice={c} />
	{/if}
{/snippet}

<ClaimFilterBar exclude={excludedFilters} />
<PaginatedTable
	paginatedResponse={claims}
	{columns}
	bind:sorting
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	onSortChange={handleSortChange}
	{loading}
	scrollable
	rowProps={{
		onClick: onRowClick,
		class: 'cursor-pointer'
	}}
	{contextSnippet}
/>
