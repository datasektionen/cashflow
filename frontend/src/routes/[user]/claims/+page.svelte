<script lang="ts">
	import type { PageProps } from './$types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn, TableRowProps } from '$lib/components/types';
	import type { Claim } from '$lib/api/types';
	import { alerts, success } from '$lib/stores/alerts';
	import { logger } from '$lib/logger';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';
	import ProfileCard from './ProfileCard.svelte';

	let { data }: PageProps = $props();

	const isOwnClaims = $derived(data.user != null && data.user.username === page.params.user);

	$effect(() => {
		if (page.url.searchParams.get('createSuccess')) {
			alerts.update((a) => [...a, success($_('expense_created'))]);
		}
	});

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
		onClick: (claim) => {
			console.log('Claim clicked:', claim);
			if (claim.type === 'expense') {
				goto(`/${data.user.username}/expenses/${claim.id}`);
			} else if (claim.type === 'invoice') {
				goto(`/${data.user.username}/invoices/${claim.id}`);
			} else {
				logger.warn('unexpected claim type');
			}
		},
		class: 'cursor-pointer'
	};

	const columns: TableColumn<Claim>[] = [
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
			header: $_('admin_expenses.columns.expense_date'),
			render: (row) => row.created_date,
			width: 'w-28'
		}
	];
</script>

{#snippet costCentres(c: Claim)}
	{@const unique = [...new Set(c.parts.map((p) => p.cost_centre))]}
	<div class="flex flex-wrap gap-1">
		{#each unique as cc}
			<span class="rounded bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
		{/each}
	</div>
{/snippet}

{#if isOwnClaims && data.user}
	<ProfileCard user={data.user} />
{/if}

<ClaimFilterBar
	costCentreItems={['Sektionslokalsgruppen']}
	secondaryCostCentreItems={['Allmänt', 'X-scapomiddag']}
	budgetLineItems={['METAdryck', 'Inköp mat']}
/>
<PaginatedTable
	paginatedResponse={data.claims}
	{columns}
	onPageChange={handlePageChange}
	onPerPageChange={handlePerPageChange}
	{rowProps}
/>
