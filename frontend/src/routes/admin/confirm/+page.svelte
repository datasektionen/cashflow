<script lang="ts">
	import type { PageProps } from './$types';
	import { type Claim, type Expense, type Invoice } from '#lib/api/types.ts';
	import { goto } from '$app/navigation';
	import { _ } from 'svelte-i18n';
	import ExpensePreview from './ExpensePreview.svelte';
	import { ScrollArea } from 'bits-ui';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data }: PageProps = $props();

	let preview: Expense | null = $state(null);

	function handleRowClick(e: Claim | Expense | Invoice) {
		// lg breakpoint = where the preview pane becomes visible; below it, navigate instead
		if (window.matchMedia('(min-width: 1024px)').matches) {
			preview = e as Expense;
		} else {
			goto(`/admin/expenses/${e.id}`);
		}
	}
</script>

<div class="flex flex-col gap-6 lg:h-[calc(100dvh-10rem)] lg:flex-row lg:overflow-hidden">
	<div class="min-w-0 flex-1 lg:min-h-0 lg:max-w-4xl lg:overflow-y-auto">
		<ClaimTable
			claims={data.claims}
			user={data.user!}
			filters={['description', 'attested', 'flagged']}
			excludeColumns={['verification', 'type', 'status']}
			rowHref={(c) => `/admin/expenses/${c.id}`}
			onRowClick={handleRowClick}
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
