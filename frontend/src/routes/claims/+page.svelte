<script lang="ts">
	import type { PageProps } from './$types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn, TableRowProps } from '$lib/components/types';
	import type { Claim, Expense } from '$lib/api/types';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';
	import ClaimStatusPills from '$lib/components/ClaimStatusPills.svelte';
	import ProfileCard from './ProfileCard.svelte';
	import { isExtraSmallLayout, isSmallLayout } from '$lib/stores/state.svelte';
	import { formatDineroAmount } from '$lib/money';
	import { api } from '$lib/api';
	import type { LeaderboardEntry, PaginatedResponse } from '../../lib/api/types';

	let range = $state(0);

	function rangeStart(r: number): string {
		const now = new Date();
		const year = now.getFullYear();
		const month = String(now.getMonth() + 1).padStart(2, '0');
		if (r === 1) return `${year}-01-01`;
		if (r === 2) return `${year}-${month}-01`;
		return '2000-01-01';
	}

	let leaderboard: Promise<PaginatedResponse<LeaderboardEntry>> = $derived(
		api.stats.leaderboard(1, 1000000, rangeStart(range), undefined, '-expense_count')
	);

	let userStats = $derived(
		Promise.all([
			api.stats.leaderboard(
				1, 1000000, rangeStart(range), undefined, '-expense_total'
			),
			api.stats.leaderboard(
				1, 1000000, rangeStart(range), undefined, '-expense_count'
			)
		]).then(([amountRes, countRes]) => {
			const username = data.user?.username;
			if (!username) return null;

			const amountIndex = amountRes.data.findIndex(
				(entry) => entry.owner.username === username
			);

			const countIndex = countRes.data.findIndex(
				(entry) => entry.owner.username === username
			);

			if (amountIndex === -1 || countIndex === -1) return null;

			const user = amountRes.data[amountIndex];

			return {
				totalAmount: user.expense_total,
				totalCount: user.expense_count,
				amountRank: amountIndex + 1,
				countRank: countIndex + 1
			};
		})
	);

	let { data }: PageProps = $props();

	const viewedUser = $derived(data.user);
	const title = $derived(viewedUser ? `${viewedUser.first_name} ${viewedUser.last_name}` : '');

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
			data.user
				? `/${data.user.username}/${claim.type === 'invoice' ? 'invoices' : 'expenses'}/${claim.id}`
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
</script>

{#snippet statusCell(c: Claim)}
	<ClaimStatusPills claim={c} />
{/snippet}

{#snippet totalCell(c: Claim)}
	<span class="tabular-nums">{formatDineroAmount(c.amount)} kr</span>
{/snippet}

{#snippet costCentres(c: Claim)}
	{@const unique = [...new Set(c.parts.map((p) => p.cost_centre))]}
	<div class="flex flex-wrap gap-1">
		{#each unique as cc}
			<span class="rounded bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
		{/each}
	</div>
{/snippet}

<h1 class="mb-4 text-xl font-bold dark:text-slate-100">{title}</h1>

{#if data.user}
	<ProfileCard user={data.user} />
{/if}

<div class="relative flex w-48 shrink-0 flex-row overflow-hidden bg-base-300 dark:bg-dark-base-300">
	<div
		class={[
			'absolute inset-y-0 w-16 bg-money-green-500 transition-all',
			range === 0 && 'left-0',
			range === 1 && 'left-16',
			range === 2 && 'left-32'
		]}
	></div>
	<button
		onclick={() => (range = 0)}
		class={[
			'z-2 w-16 cursor-pointer py-1.5 text-center text-xs font-medium whitespace-nowrap uppercase transition-colors',
			range === 0 ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
		]}>{$_('leaderboard.all_time')}</button
	>
	<button
		onclick={() => (range = 1)}
		class={[
			'z-2 w-16 cursor-pointer py-1.5 text-center text-xs font-medium whitespace-nowrap uppercase transition-colors',
			range === 1 ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
		]}>{$_('leaderboard.year')}</button
	>
	<button
		onclick={() => (range = 2)}
		class={[
			'z-2 w-16 cursor-pointer py-1.5 text-center text-xs font-medium whitespace-nowrap uppercase transition-colors',
			range === 2 ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
		]}>{$_('leaderboard.month')}</button
	>
</div>
<br />

{#await userStats}
    <p>Laddar statistik...</p>
{:then stats}
    {#if stats}
        <div class="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
            <div class="rounded-lg bg-base-200 p-4 dark:bg-dark-base-200">
                <p class="text-sm">Totalt Cashflowat</p>
                <p class="text-2xl font-bold">
                    {formatDineroAmount(stats.totalAmount)} kr
                </p>
            </div>

            <div class="rounded-lg bg-base-200 p-4 dark:bg-dark-base-200">
                <p class="text-sm">Antal utlägg</p>
                <p class="text-2xl font-bold">
                    {stats.totalCount}
                </p>
            </div>
		</div>
		<div class="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">

            <div class="rounded-lg bg-base-200 p-4 dark:bg-dark-base-200">
                <p class="text-sm">Placering efter belopp</p>
                <p class="text-2xl font-bold">
                    #{stats.amountRank}
                </p>
            </div>

            <div class="rounded-lg bg-base-200 p-4 dark:bg-dark-base-200">
                <p class="text-sm">Placering efter antal</p>
                <p class="text-2xl font-bold">
                    #{stats.countRank}
                </p>
            </div>
        </div>
    {:else}
        <p>Ingen statistik tillgänglig för denna period.</p>
    {/if}
{:catch error}
    <p>Kunde inte ladda statistiken.</p>
{/await}

<ClaimFilterBar includeChecks={false} exclude={['voucher_series', 'voucher_number']} />
<PaginatedTable
	paginatedResponse={data.claims}
	{columns}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{rowProps}
/>
