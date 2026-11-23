<script lang="ts">
	import { claimColumns } from '#lib/components/TableCells.svelte';
	import type { PageProps } from './$types';
	import { _ } from 'svelte-i18n';
	import PaginatedTable from '#lib/components/PaginatedTable.svelte';
	import type { TableRowProps } from '#lib/components/types.ts';
	import type { Claim } from '#lib/api/types.ts';
	import ClaimFilterBar from '#lib/components/ClaimFilterBar.svelte';
	import ProfileCard from './ProfileCard.svelte';
	import UserAvatar from '#lib/components/UserAvatar.svelte';
	import StatCard from './StatCard.svelte';
	import { latest } from '#lib/latest.svelte.ts';
	import RangeControl, { rangeStart } from '../stats/RangeControl.svelte';
	import { formatDineroAmount } from '#lib/money.ts';
	import { api } from '#lib/api/index.ts';

	let { data }: PageProps = $props();

	let range = $state(0);

	const stats = latest(() => api.stats.userLeaderboard(data.user.username, rangeStart(range)));

	const rowProps: TableRowProps<Claim> = {
		href: (claim) =>
			`/${data.user.username}/${claim.type === 'invoice' ? 'invoices' : 'expenses'}/${claim.id}`,
		class: 'cursor-pointer'
	};

	const columns = $derived(claimColumns($_));
</script>

<header class="flex flex-wrap items-center gap-x-6 gap-y-3 pb-6">
	<UserAvatar username={data.user.username} class="size-12" />
	<div class="mr-auto flex min-w-0 flex-col">
		<h1 class="text-3xl font-bold tracking-tight wrap-break-word">
			{data.user.first_name}
			{data.user.last_name}
		</h1>
		<p class="truncate text-sm text-muted-foreground">{data.user.email}</p>
	</div>
	<RangeControl bind:range />
</header>

<div class="flex flex-col gap-6">
	<ProfileCard user={data.user} />

	<div class="flex flex-col gap-4">
		{#if stats.error}
			<p class="text-sm text-danger-text">{$_('claims.error')}</p>
		{:else}
			{@const s = stats.value}
			<div
				class={[
					'grid grid-cols-2 gap-4 transition-opacity md:grid-cols-4',
					stats.loading && s && 'opacity-60'
				]}
			>
				<StatCard
					label={$_('claims.total_cashflow')}
					value={s && `${formatDineroAmount(s.expense_total)} kr`}
				/>
				<StatCard label={$_('claims.total_cashflows')} value={s?.expense_count} />
				<StatCard
					label={$_('claims.amount_rank')}
					value={s && (s.amount_rank ? `#${s.amount_rank}` : '–')}
				/>
				<StatCard
					label={$_('claims.count_rank')}
					value={s && (s.count_rank ? `#${s.count_rank}` : '–')}
				/>
			</div>
		{/if}
	</div>

	<div class="flex flex-col gap-4">
		<ClaimFilterBar
			includeChecks={false}
			exclude={['voucher_series', 'verification', 'invoice_number', 'reimbursement']}
		/>
		<PaginatedTable paginatedResponse={data.claims} {columns} {rowProps} />
	</div>
</div>
