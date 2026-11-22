<script lang="ts" module>
	import type { Dinero } from 'dinero.js';
	import type { Claim, Expense, Invoice, Profile } from '#lib/api/types.ts';
	import { claimTotal, formatDineroAmount } from '#lib/money.ts';
	import CostCentreCell from './CostCentreCell.svelte';
	import UserCell from './UserCell.svelte';
	import ClaimStatus from './claim/ClaimStatus.svelte';
	import type { TableColumn } from './types';
	import { byLayout } from '#lib/stores/state.svelte.ts';

	type Parts = { parts: { cost_centre: string; amount: Dinero<number, 'SEK'> }[] };
	type Row = Claim | Expense | Invoice;
	type Shared = 'id' | 'description' | 'owner' | 'cost_centres' | 'total' | 'status';

	export { idCell, amountCell, ownerCell, costCentreCell, statusCell };

	/** Columns shared by the claim tables; pages pick and override them. */
	export function claimColumnDefs(
		t: (key: string) => string
	): Record<Shared, TableColumn<Row>> & { type: TableColumn<Claim> } {
		return {
			id: {
				id: 'id',
				header: t('admin_expenses.columns.id'),
				renderSnippet: idCell,
				width: 'w-16',
				sorting: ['-id', 'id']
			},
			type: {
				id: 'type',
				header: t('claims_type'),
				render: (row) => t(row.type),
				width: 'w-24',
				sorting: ['-type', 'type']
			},
			description: {
				id: 'description',
				header: t('admin_expenses.columns.description'),
				render: (row) => row.description,
				sorting: ['-description', 'description']
			},
			owner: {
				id: 'owner',
				header: t('admin_expenses.columns.owner'),
				renderSnippet: ownerCell,
				sorting: ['-user', 'user']
			},
			cost_centres: {
				id: 'cost_centres',
				header: t('admin_expenses.columns.cost_centres'),
				renderSnippet: costCentreCell,
				width: 'w-48',
				sorting: ['-cost_centre', 'cost_centre']
			},
			total: {
				id: 'total',
				header: t('admin_expenses.columns.total'),
				renderSnippet: amountCell,
				width: 'w-32',
				align: 'right',
				sorting: ['-total', 'total']
			},
			status: {
				id: 'status',
				header: t('admin_expenses.columns.status'),
				renderSnippet: statusCell,
				width: 'w-56'
			}
		};
	}

	/** Columns of the claim lists on the profile and admin user pages. */
	export function claimColumns(t: (key: string) => string): TableColumn<Claim>[] {
		const col = claimColumnDefs(t);
		return byLayout<Claim>(
			[
				col.type,
				col.description,
				col.cost_centres,
				{
					id: 'created_date',
					header: t('date'),
					render: (row) => row.created_date,
					width: 'w-32',
					sorting: ['-created_date', 'created_date']
				},
				col.total,
				{ ...col.status, width: 'w-40' }
			],
			{ xs: ['description', 'total'], sm: ['type', 'description', 'total', 'status'] }
		);
	}
</script>

{#snippet idCell(row: { id: number })}
	<span class="text-xs text-muted-foreground tabular-nums">#{row.id}</span>
{/snippet}

{#snippet amountCell(row: Parts)}
	<span class="tabular-nums">{formatDineroAmount(claimTotal(row))} kr</span>
{/snippet}

{#snippet ownerCell(row: { owner: Profile })}
	<UserCell user={row.owner} />
{/snippet}

{#snippet costCentreCell(row: Parts)}
	<CostCentreCell parts={row.parts} />
{/snippet}

{#snippet statusCell(row: Row)}
	<ClaimStatus claim={row} />
{/snippet}
