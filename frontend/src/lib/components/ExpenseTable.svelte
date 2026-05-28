<script lang="ts">
	import type { Expense, PaginatedResponse } from '$lib/api/types';
	import { Pagination } from 'bits-ui';
	import { ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';

	interface Props {
		expenses: PaginatedResponse<Expense>;
		onPageChange: (page: number) => void;
		onPerPageChange: (perPage: number) => void;
	}
	let { expenses, onPageChange, onPerPageChange }: Props = $props();

	const perPageOptions = [10, 20, 50, 100];

	const rangeStart = $derived(
		expenses.pagination.total === 0
			? 0
			: (expenses.pagination.page - 1) * expenses.pagination.perPage + 1
	);
	const rangeEnd = $derived(
		Math.min(expenses.pagination.page * expenses.pagination.perPage, expenses.pagination.total)
	);

	type Column<T> = {
		key: keyof T;
		header: string;
		render: (row: T) => string;
		width: string;
	};
	const columns: Column<Expense>[] = $derived([
		{
			key: 'id',
			header: $_('admin_expenses.columns.id'),
			render: (e) => e.id.toString(),
			width: 'w-16'
		},
		{
			key: 'verification',
			header: $_('admin_expenses.columns.voucher'),
			render: (e) => e.verification,
			width: 'w-32'
		},
		{
			key: 'description',
			header: $_('admin_expenses.columns.description'),
			render: (e) => e.description,
			width: 'w-auto'
		},
		{
			key: 'owner',
			header: $_('admin_expenses.columns.owner'),
			render: (e) => e.owner.first_name + ' ' + e.owner.last_name,
			width: 'w-56'
		},
		{
			key: 'expense_date',
			header: $_('admin_expenses.columns.expense_date'),
			render: (e) => e.expense_date,
			width: 'w-32'
		}
	]);
</script>

<div class="border border-base-500 p-2 dark:border-dark-base-200">
	<table class="w-full table-fixed">
		<thead>
			<tr>
				{#each columns as column}
					<th
						class="{column.width} px-4 py-3 text-left text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
					>
						{column.header}
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each expenses.data as expense}
				<tr
					class="border-b border-b-base-400 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200"
				>
					{#each columns as column}
						<td class="px-4 py-3">
							{column.render(expense)}
						</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>

	<div class="mt-4 flex flex-row items-center justify-center md:justify-between">
		<div class="hidden text-sm text-base-subtle md:flex dark:text-dark-base-subtle">
			{$_('admin_expenses.pagination.showing', {
				values: {
					start: rangeStart,
					end: rangeEnd,
					total: expenses.pagination.total.toLocaleString()
				}
			})}
		</div>

		<Pagination.Root
			class="flex flex-row items-center space-x-2"
			count={expenses.pagination.total}
			perPage={expenses.pagination.perPage}
			page={expenses.pagination.page}
			{onPageChange}
		>
			{#snippet children({ pages, range })}
				<Pagination.PrevButton
					class="group size-8 cursor-pointer items-center not-disabled:hover:bg-base-600 disabled:cursor-not-allowed disabled:text-base-subtle not-disabled:dark:hover:bg-dark-base-200 dark:disabled:text-dark-base-subtle"
				>
					<ChevronLeft class="m-auto size-4 group-disabled:opacity-50" />
				</Pagination.PrevButton>
				{#each pages as page (page.key)}
					{#if page.type === 'ellipsis'}
						<div class="size-8">...</div>
					{:else}
						<Pagination.Page
							class="size-8 cursor-pointer items-center justify-center text-sm hover:bg-base-600 data-selected:bg-base-600 dark:hover:bg-dark-base-200 dark:data-selected:bg-dark-base-200"
							{page}
						>
							{page.value}
						</Pagination.Page>
					{/if}
				{/each}

				<Pagination.NextButton
					class="group size-8 cursor-pointer items-center not-disabled:hover:bg-base-600 disabled:cursor-not-allowed disabled:text-base-subtle not-disabled:dark:hover:bg-dark-base-200 dark:disabled:text-dark-base-subtle"
				>
					<ChevronRight class="m-auto size-4 group-disabled:opacity-50" />
				</Pagination.NextButton>
			{/snippet}
		</Pagination.Root>

		<div class="hidden flex-row items-center space-x-2 text-sm md:flex">
			<label for="per-page" class="text-base-subtle dark:text-dark-base-subtle">
				{$_('admin_expenses.pagination.show')}
			</label>
			<select
				id="per-page"
				value={expenses.pagination.perPage}
				onchange={(e) => onPerPageChange(Number((e.target as HTMLSelectElement).value))}
				class="bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22 viewBox=%220 0 24 24%22 fill=%22none%22 stroke=%22currentColor%22 stroke-width=%222%22 stroke-linecap=%22round%22 stroke-linejoin=%22round%22><polyline points=%226 9 12 15 18 9%22/></svg>')] cursor-pointer appearance-none rounded border border-base-500 bg-transparent bg-position-[right_0.5rem_center] bg-no-repeat py-1 pr-7 pl-2 dark:border-dark-base-200"
			>
				{#each perPageOptions as option}
					<option value={option}>{option}</option>
				{/each}
			</select>
		</div>
	</div>
</div>
