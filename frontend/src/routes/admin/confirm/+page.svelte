<script lang="ts">
	import type { PageProps } from './$types';
	import { _ } from 'svelte-i18n';
	import { CircleCheck } from '@lucide/svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { Claim, Expense, Invoice } from '#lib/api/types.ts';
	import { latest } from '#lib/latest.svelte.ts';
	import { isMediumLayout } from '#lib/stores/state.svelte.ts';
	import { EmptyState } from '#lib/components/ui/index.ts';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';
	import ExpensePreview from './ExpensePreview.svelte';

	let { data }: PageProps = $props();

	const filtered = $derived(
		[...page.url.searchParams.keys()].some((k) => !['page', 'per_page', 'sorting'].includes(k))
	);
	const list = latest(() => data.claims);

	let preview: Expense | null = $state(null);

	function handleRowClick(e: Claim | Expense | Invoice) {
		if (isMediumLayout.current) goto(`/admin/expenses/${e.id}`);
		else preview = e as Expense;
	}
</script>

{#if list.value?.pagination.total === 0 && !filtered}
	<EmptyState icon={CircleCheck} title={$_('tasks.empty')} class="max-w-4xl" />
{:else}
	<div class="flex flex-col gap-6 lg:min-h-0 lg:flex-1 lg:flex-row lg:overflow-hidden">
		<div class="min-w-0 lg:min-h-0 lg:flex-[3] lg:overflow-y-auto">
			<ClaimTable
				claims={data.claims}
				user={data.user}
				filters={['description', 'attested', 'flagged']}
				excludeColumns={['verification', 'type', 'status']}
				rowHref={(c) => `/admin/expenses/${c.id}`}
				onRowClick={handleRowClick}
				rowClass={(c) => (preview?.id === c.id ? 'bg-muted' : '')}
				layout={{
					xs: ['description', 'amount'],
					sm: ['description', 'owner', 'amount'],
					md: null,
					// The preview pane shows from lg up and squeezes the table below 2xl
					lg: ['description', 'owner', 'amount']
				}}
			/>
		</div>

		<div class="hidden min-h-0 lg:flex lg:flex-[2]">
			{#if preview}
				{#key preview.id}
					<ExpensePreview
						expenseId={preview.id}
						currentUser={data.user ?? undefined}
						afterConfirm={async () => {
							// Moves on to the next expense in the list, keeping its filters and order
							const { data: rows } = await data.claims;
							preview = (rows[0] as Expense | undefined) ?? null;
						}}
					/>
				{/key}
			{:else}
				<EmptyState title={$_('admin_confirmable.preview.empty')} class="w-full" />
			{/if}
		</div>
	</div>
{/if}
