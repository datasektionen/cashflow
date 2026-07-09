<script lang="ts">
	import type { PageProps } from './$types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import type { Claim } from '$lib/api/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import ClaimFilterBar from '$lib/components/ClaimFilterBar.svelte';
	import ExpensePreview from './ExpensePreview.svelte';
	import UserLink from '$lib/components/UserLink.svelte';
	import { ScrollArea } from 'bits-ui';

	let { data }: PageProps = $props();

	let loading = $state(false);

	const columns: TableColumn<Claim>[] = $derived([
		{
			id: 'description',
			header: $_('admin_confirmable.columns.description'),
			render: (c) => c.description,
			width: ''
		},
		{
			id: 'owner',
			header: $_('admin_confirmable.columns.owner'),
			renderSnippet: ownerCell,
			width: 'w-40'
		}
	]);

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

	let preview: Claim | null = $state(null);

	function handleRowClick(c: Claim) {
		// lg breakpoint = where the preview pane becomes visible; below it, navigate instead
		if (window.matchMedia('(min-width: 1024px)').matches) {
			preview = c;
		} else {
			goto(`/admin/expenses/${c.id}`);
		}
	}
</script>

{#snippet ownerCell(c: Claim)}
	<UserLink user={c.owner} />
{/snippet}

{#snippet idCell(c: Claim)}
	<div class="flex flex-row items-center">
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">#</span>
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{c.id}</span>
	</div>
{/snippet}

{#snippet statusCell(c: Claim)}
	<div class="flex gap-3">
		{#if c.is_paid}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-600 dark:bg-money-green-400"
				></span>
				{$_('expense_paid')}
			</span>
		{:else if c.is_confirmed}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-500 dark:bg-money-green-400"
				></span>
				{$_('expense_confirmed')}
			</span>
		{:else if c.is_attested}
			<span class="flex items-center gap-1.5 text-xs">
				<span
					class="inline-block size-1.5 shrink-0 rounded-full bg-money-green-400 dark:bg-money-green-500"
				></span>
				{$_('expense_attested')}
			</span>
		{:else}
			<span class="flex items-center gap-1.5 text-xs text-base-subtle dark:text-dark-base-subtle">
				<span class="inline-block size-1.5 shrink-0 rounded-full bg-base-400 dark:bg-dark-base-400"
				></span>
				{$_('expense_status.unconfirmed')}
			</span>
		{/if}
	</div>
{/snippet}

<!-- height = viewport - navbar (4rem) - main's py-4 (2rem) - page-title header (~4rem) -->
<div class="flex flex-col gap-6 lg:h-[calc(100dvh-10rem)] lg:flex-row lg:overflow-hidden">
	<!-- Table column: full width on small screens, constrained on large to leave room on the right -->
	<div class="min-w-0 flex-1 lg:min-h-0 lg:max-w-4xl lg:overflow-y-auto">
		<ClaimFilterBar
			costCentreItems={['Sektionslokalsgruppen']}
			secondaryCostCentreItems={['Allmänt', 'X-scapomiddag']}
			budgetLineItems={['METAdryck', 'Inköp mat']}
		/>
		<PaginatedTable
			paginatedResponse={data.claims}
			columns={[
				{
					id: 'id',
					header: $_('admin_confirmable.columns.id'),
					renderSnippet: idCell,
					width: 'w-16'
				},
				...columns,
				{
					id: 'is_confirmed',
					header: $_('admin_confirmable.columns.status'),
					renderSnippet: statusCell,
					width: 'w-28'
				}
			]}
			onPageChange={handlePageChange}
			onPerPageChange={handlePerPageChange}
			{loading}
			scrollable
			rowProps={{
				onClick: handleRowClick,
				class: (c: Claim) =>
					preview && c.id === preview.id
						? 'cursor-pointer bg-base-200 dark:bg-dark-base-200'
						: 'cursor-pointer'
			}}
		/>
	</div>

	<div class="hidden min-h-0 flex-1 lg:block lg:max-w-2xl">
		<ScrollArea.Root class="relative h-full w-full overflow-hidden">
			<ScrollArea.Viewport class="h-full w-full">
				<div class="px-8 pb-8">
					{#if !preview}
						<div class="flex h-full items-center justify-center py-24">
							<p class="text-sm text-base-subtle dark:text-dark-base-subtle">
								{$_('admin_confirmable.preview.empty')}
							</p>
						</div>
					{:else}
						{#key preview.id}
							<ExpensePreview expenseId={preview.id} currentUser={data.user ?? undefined} />
						{/key}
					{/if}
				</div>
			</ScrollArea.Viewport>

			<ScrollArea.Scrollbar
				orientation="vertical"
				class="hover:bg-dark-10 data-[state=visible]:animate-in data-[state=hidden]:animate-out data-[state=hidden]:fade-out-0 data-[state=visible]:fade-in-0 flex w-2.5 touch-none rounded-none border-l border-l-transparent bg-base-subtle p-px transition-all duration-200 select-none hover:w-3 dark:bg-dark-base-subtle"
			>
				<ScrollArea.Thumb class="flex-1 rounded-none bg-base-400 dark:bg-dark-base-400" />
			</ScrollArea.Scrollbar>
		</ScrollArea.Root>
	</div>
</div>
