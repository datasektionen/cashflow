<script lang="ts">
	import type { PageProps } from './$types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn, TableRowProps } from '$lib/components/types';
	import type { Claim } from '$lib/api/types';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';
	import ClaimStatusPills from '$lib/components/ClaimStatusPills.svelte';
	import { isExtraSmallLayout, isSmallLayout } from '$lib/stores/state.svelte';
	import { formatBankAccount } from '$lib/bankAccount';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import CopyableValue from '$lib/components/ui/CopyableValue.svelte';
	import { mayPay } from '$lib/auth';
	import ClaimContextMenu from '$lib/components/ClaimContextMenu.svelte';

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

	const rowProps: TableRowProps<Claim> = {
		href: (claim) =>
			data.viewedUser
				? `/admin/${claim.type === 'invoice' ? 'invoices' : 'expenses'}/${claim.id}`
				: '',
		class: 'cursor-pointer'
	};

	const columns: TableColumn<Claim>[] = $derived(
		(
			[
				{
					id: 'type',
					header: $_('claims_type'),
					render: (row) => $_(row.type),
					width: 'w-24'
				},
				{
					id: 'description',
					header: $_('admin_invoices.columns.description'),
					render: (row) => row.description,
					width: ''
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
					render: (row) => row.created_date,
					width: 'w-28'
				},
				{
					id: 'total',
					header: $_('admin_expenses.columns.total'),
					renderSnippet: totalCell,
					width: 'w-28'
				},
				{
					id: 'status',
					header: $_('admin_expenses.columns.status'),
					renderSnippet: statusCell,
					width: 'w-40'
				}
			] as TableColumn<Claim>[]
		).filter((col) => {
			if (isExtraSmallLayout.current) return ['description', 'total'].includes(col.id);
			if (isSmallLayout.current) return ['type', 'description', 'total', 'status'].includes(col.id);
			return true;
		})
	);

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});

	const formattedAccount = $derived(
		data.viewedUser.bank_info
			? formatBankAccount(
					data.viewedUser.bank_info.sorting_number,
					data.viewedUser.bank_info.bank_account
				)
			: null
	);
</script>

{#snippet contextSnippet(claim: Claim)}
	<ClaimContextMenu {claim} kind={claim.type} user={data.user} />
{/snippet}

{#snippet statusCell(c: Claim)}
	<ClaimStatusPills claim={c} />
{/snippet}

{#snippet totalCell(c: Claim)}
	<span class="tabular-nums">{fmt.format(parseFloat(c.amount))} kr</span>
{/snippet}

{#snippet costCentres(c: Claim)}
	{@const unique = [...new Set(c.parts.map((p) => p.cost_centre))]}
	<div class="flex flex-wrap gap-1">
		{#each unique as cc}
			<span class="rounded bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
		{/each}
	</div>
{/snippet}

<div
	class="mb-6 flex flex-wrap items-center gap-6 border border-base-400 p-4 dark:border-dark-base-200"
>
	<div class="flex items-center gap-4">
		<UserAvatar username={data.viewedUser.username} class="size-16" />
		<div>
			<div class="font-semibold">{data.viewedUser.first_name} {data.viewedUser.last_name}</div>
			<div class="text-sm text-base-subtle dark:text-dark-base-subtle">{data.viewedUser.email}</div>
		</div>
	</div>

	{#if mayPay(data.user)}
		<div class="flex flex-col text-sm text-base-subtle dark:text-dark-base-subtle">
			<p class="pb-2 pl-2.5">{data.viewedUser.bank_info.bank_name}</p>
			{#if formattedAccount != null}
				<CopyableValue value={formattedAccount} display={formattedAccount} />
			{/if}
		</div>
	{/if}
</div>

<ClaimFilterBar includeChecks={false} exclude={['voucher_series', 'voucher_number']} />
<PaginatedTable
	paginatedResponse={data.claims}
	{columns}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{rowProps}
	{contextSnippet}
/>
