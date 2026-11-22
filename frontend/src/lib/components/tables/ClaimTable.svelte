<script lang="ts">
	import { _ } from 'svelte-i18n';
	import type { Claim, Expense, Invoice, PaginatedResponse, User } from '#lib/api/types.ts';
	import { byLayout, type Layouts } from '#lib/stores/state.svelte.ts';
	import ClaimFilterBar, { type Filter } from '../ClaimFilterBar.svelte';
	import ClaimContextMenu from '../ClaimContextMenu.svelte';
	import PaginatedTable from '../PaginatedTable.svelte';
	import { claimColumnDefs } from '../TableCells.svelte';
	import type { TableColumn } from '../types';

	type AnyClaim = Claim | Expense | Invoice;
	// due_date is opt-in: only invoice lists have it
	type ColumnOption =
		| 'verification'
		| 'id'
		| 'type'
		| 'description'
		| 'owner'
		| 'cost_centres'
		| 'date'
		| 'due_date'
		| 'amount'
		| 'status'
		| '__all__';

	const getType = (c: AnyClaim) =>
		'type' in c ? c.type : 'expense_date' in c ? 'expense' : 'invoice';
	const getDate = (c: AnyClaim) =>
		'expense_date' in c && c.expense_date
			? c.expense_date
			: 'invoice_date' in c
				? c.invoice_date
				: '';

	let {
		claims,
		user,
		rowHref = (c) => `/admin/${getType(c) === 'expense' ? 'expenses' : 'invoices'}/${c.id}`,
		onRowClick,
		rowClass,
		filters,
		includeColumns = ['__all__'],
		excludeColumns = [],
		layout = { xs: ['description', 'amount'] }
	}: {
		claims: Promise<PaginatedResponse<AnyClaim>>;
		user: User | null;
		rowHref?: (c: AnyClaim) => string;
		// Overrides plain-click behaviour; rowHref is still used for opening in a new tab
		onRowClick?: (c: AnyClaim) => void;
		rowClass?: (c: AnyClaim) => string;
		filters: Filter[];
		includeColumns?: ColumnOption[];
		excludeColumns?: ColumnOption[];
		// Columns kept per breakpoint, see byLayout
		layout?: Layouts;
	} = $props();

	const col = $derived(claimColumnDefs($_));
	const columns: TableColumn<AnyClaim>[] = $derived.by(() => {
		const all: TableColumn<AnyClaim>[] = [
			{
				id: 'verification',
				header: $_('admin_expenses.columns.voucher'),
				renderSnippet: voucherCell,
				width: 'w-28',
				sorting: ['-verification', 'verification']
			},
			col.id,
			{
				id: 'type',
				header: $_('claims_type'),
				render: (c) => $_(getType(c)),
				width: 'w-24',
				sorting: ['-type', 'type']
			},
			{ ...col.description, width: 'min-w-48' },
			col.owner,
			col.cost_centres,
			{
				id: 'date',
				header: $_('date'),
				render: getDate,
				width: 'w-28',
				sorting: ['-date', 'date']
			},
			{
				id: 'due_date',
				header: $_('admin_invoices.columns.due_date'),
				render: (c) => ('due_date' in c ? (c.due_date ?? '') : ''),
				width: 'w-28',
				sorting: ['-due_date', 'due_date']
			},
			{ ...col.total, id: 'amount', header: $_('amount') },
			col.status
		];
		const shown = all.filter((c) => {
			const id = c.id as ColumnOption;
			const included =
				includeColumns.includes(id) || (includeColumns.includes('__all__') && id !== 'due_date');
			return included && !excludeColumns.includes(id);
		});
		return byLayout(shown, layout);
	});

	const allFilters: Filter[] = [
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
	];
	const excludedFilters = $derived(allFilters.filter((f) => !filters.includes(f)));
</script>

{#snippet contextSnippet(c: AnyClaim)}
	<ClaimContextMenu claim={c} kind={getType(c)} {user} />
{/snippet}

{#snippet voucherCell(c: AnyClaim)}
	<span class="font-mono text-xs">{c.voucher ?? '–'}</span>
{/snippet}

<ClaimFilterBar exclude={excludedFilters} />
<PaginatedTable
	paginatedResponse={claims}
	{columns}
	scrollable
	rowProps={{ href: rowHref, onClick: onRowClick, class: rowClass }}
	{contextSnippet}
/>
