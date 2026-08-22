<!--
@component
A table that accepts either a paginated response or other data. Uses bits-ui Pagination
-->
<script lang="ts" generics="T">
	import type { PaginatedResponse } from '$lib/api/types';
	import type { TableColumn, TableRowProps } from './types';
	import { Pagination } from 'bits-ui';
	import {
		ChevronDown,
		ChevronLeft,
		ChevronRight,
		ChevronsUpDown,
		ChevronUp
	} from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { isExtraSmallLayout, isSmallLayout } from '$lib/stores/state.svelte';
	import { goto } from '$app/navigation';

	interface Props {
		paginatedResponse?: PaginatedResponse<T>;
		data?: T[];
		columns: TableColumn<T>[];
		onPageChange?: (page: number) => void;
		onPerPageChange?: (perPage: number) => void;
		loading?: boolean;
		rowProps?: TableRowProps<T>;
		scrollable?: boolean;
		sorting?: string | null;
		onSortChange?: (sort: string) => void;
	}

	let {
		paginatedResponse,
		data,
		columns,
		onPageChange,
		onPerPageChange,
		loading,
		rowProps,
		scrollable = false,
		sorting = $bindable(null),
		onSortChange
	}: Props = $props();

	const resolved = $derived<PaginatedResponse<T>>(
		paginatedResponse ?? {
			data: data ?? [],
			pagination: { total: data?.length ?? 0, page: 1, perPage: data?.length ?? 0, totalPages: 1 }
		}
	);

	const perPageOptions = [15, 25, 50, 100];

	function resolveRowClass(row: T): string | undefined {
		const c = rowProps?.class;
		return typeof c === 'function' ? c(row) : c;
	}

	function handleRowClick(e: MouseEvent, row: T) {
		if ((e.target as HTMLElement).closest('a, button')) return;
		if (rowProps?.href) {
			const href = rowProps.href(row);
			if (e.metaKey || e.ctrlKey || e.shiftKey) {
				window.open(href, '_blank', 'noopener');
			} else if (!e.altKey) {
				goto(href);
			}
		} else {
			rowProps?.onClick?.(row);
		}
	}

	function handleRowAuxClick(e: MouseEvent, row: T) {
		if (e.button !== 1) return;
		if ((e.target as HTMLElement).closest('a, button')) return;
		if (rowProps?.href) {
			window.open(rowProps.href(row), '_blank', 'noopener');
		}
	}

	const rangeStart = $derived(
		resolved.pagination.total === 0
			? 0
			: (resolved.pagination.page - 1) * resolved.pagination.perPage + 1
	);
	const rangeEnd = $derived(
		Math.min(resolved.pagination.page * resolved.pagination.perPage, resolved.pagination.total)
	);

	const handleSortChange = (column: TableColumn<T>) => {
		if (!column.sorting) return;
		// Cycle through the column's sort options (desc first, then asc), then
		// back to unsorted.
		const idx = sorting ? column.sorting.indexOf(sorting) : -1;
		if (idx === -1) {
			sorting = column.sorting[0];
		} else if (idx === column.sorting.length - 1) {
			sorting = null;
		} else {
			sorting = column.sorting[idx + 1];
		}
		onSortChange?.(sorting ?? '');
	};

	let expanded: number | null = $state(null);
</script>

<div class="border border-base-500 p-2 dark:border-dark-base-200">
	<div class="relative">
		<div class="overflow-hidden">
			<table class="w-full table-fixed text-sm">
				<thead>
					<tr>
						{#each columns as column}
							<th
								class={[
									column.width,
									'px-4 py-3 text-left text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle',
									column.sorting && 'cursor-pointer'
								]}
								onclick={column.sorting ? () => handleSortChange(column) : null}
							>
								<span class="flex min-w-0 flex-row items-center gap-2">
									<span class="truncate">{column.header}</span>
									{#if column.sorting}
										{#if !sorting || !column.sorting.includes(sorting)}
											<ChevronsUpDown class="size-4 shrink-0" />
										{:else if column.sorting.indexOf(sorting) === 0}
											<ChevronDown class="size-4 shrink-0" />
										{:else}
											<ChevronUp class="size-4 shrink-0" />
										{/if}
									{/if}
								</span>
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each resolved.data as row, i}
						<tr
							class={[
								'h-12 border-b border-b-base-400 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200',
								resolveRowClass(row)
							]}
							onclick={(e) => {
								if (rowProps?.expandedSnippet) {
									expanded = expanded === i ? null : i;
								}
								handleRowClick(e, row);
							}}
							onauxclick={(e) => handleRowAuxClick(e, row)}
						>
							{#each columns as column, ci}
								<td class={['overflow-hidden px-4', !column.renderSnippet && 'truncate']}>
									{#if ci === 0 && rowProps?.href}
										<a href={rowProps.href(row)}>
											{#if column.renderSnippet}
												{@render column.renderSnippet(row)}
											{:else}
												{column.render?.(row) ?? ''}
											{/if}
										</a>
									{:else if column.renderSnippet}
										{@render column.renderSnippet(row)}
									{:else}
										{column.render?.(row) ?? ''}
									{/if}
								</td>
							{/each}
							{#if rowProps?.expandedSnippet && !isExtraSmallLayout.current}
								<td>
									{#if expanded === i}
										<ChevronUp />
									{:else}
										<ChevronDown />
									{/if}
								</td>
							{/if}
						</tr>
						{#if rowProps?.expandedSnippet && expanded === i}
							<tr
								class="h-12 border-b border-b-base-400 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200"
							>
								<td colspan={columns.length} class="px-4 py-2">
									{@render rowProps.expandedSnippet(row)}
								</td>
							</tr>
						{/if}
					{/each}
					{#each { length: Math.max(0, resolved.pagination.perPage - resolved.data.length) } as _}
						<tr class="h-12 border-b border-b-base-400 dark:border-dark-base-150">
							{#each columns as column}
								<td class="px-4">&nbsp;</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<!-- Loading overlay -->
		<div
			class={[
				'absolute top-0 left-0 z-20 flex size-full items-center justify-center bg-white/30 text-money-green-500 backdrop-blur-sm transition-opacity duration-200 dark:bg-black/30',
				loading ? 'opacity-100' : 'pointer-events-none opacity-0'
			]}
		>
			<CashSpinner />
		</div>
	</div>

	<div
		class={[
			'mt-4 flex flex-row items-center justify-center md:justify-between',
			scrollable && 'sticky bottom-0 bg-base-200 py-2 dark:bg-dark-base-100'
		]}
	>
		<div class="hidden text-sm text-base-subtle md:flex dark:text-dark-base-subtle">
			{$_('admin_paginatedResponse.pagination.showing', {
				values: {
					start: rangeStart,
					end: rangeEnd,
					total: resolved.pagination.total.toLocaleString()
				}
			})}
		</div>

		<Pagination.Root
			class="flex max-w-full flex-row items-center space-x-1 md:space-x-2"
			count={resolved.pagination.total}
			perPage={resolved.pagination.perPage}
			page={resolved.pagination.page}
			siblingCount={isSmallLayout.current ? 0 : 1}
			onPageChange={onPageChange ?? (() => {})}
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
				{$_('admin_paginatedResponse.pagination.show')}
			</label>
			<select
				id="per-page"
				value={resolved.pagination.perPage}
				onchange={(e) => onPerPageChange?.(Number((e.target as HTMLSelectElement).value))}
				class="bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22 viewBox=%220 0 24 24%22 fill=%22none%22 stroke=%22currentColor%22 stroke-width=%222%22 stroke-linecap=%22round%22 stroke-linejoin=%22round%22><polyline points=%226 9 12 15 18 9%22/></svg>')] cursor-pointer appearance-none rounded border border-base-500 bg-transparent bg-position-[right_0.5rem_center] bg-no-repeat py-1 pr-7 pl-2 dark:border-dark-base-200"
			>
				{#each perPageOptions as option}
					<option value={option}>{option}</option>
				{/each}
			</select>
		</div>
	</div>
</div>
