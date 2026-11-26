<!--
@component
A table for a paginated response, with page, page size and sorting kept in the URL.
-->
<script lang="ts" generics="T">
	import type { PaginatedResponse } from '#lib/api/types.ts';
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
	import { latest } from '#lib/latest.svelte.ts';
	import { Button, Card, Select, Skeleton, Table } from '#lib/components/ui/index.ts';
	import { isExtraSmallLayout, isSmallLayout } from '#lib/stores/state.svelte.ts';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import type { Snippet } from 'svelte';

	interface Props {
		paginatedResponse: Promise<PaginatedResponse<T>>;
		columns: TableColumn<T>[];
		rowProps?: TableRowProps<T>;
		scrollable?: boolean;
		contextSnippet?: Snippet<[T]>;
	}

	let {
		paginatedResponse,
		columns,
		rowProps,
		scrollable = false,
		contextSnippet
	}: Props = $props();

	// Written on click so the header updates before navigation finishes
	let sorting = $derived(page.url.searchParams.get('sorting'));

	function updateUrl(update: (params: URLSearchParams) => void) {
		const url = new URL(page.url.href);
		update(url.searchParams);
		goto(url, { reset: false });
	}

	const changePage = (p: number) => updateUrl((params) => params.set('page', String(p)));
	const changePerPage = (perPage: number) =>
		updateUrl((params) => {
			params.set('per_page', String(perPage));
			params.set('page', '1');
		});
	const changeSort = (sort: string) =>
		updateUrl((params) => {
			if (sort) params.set('sorting', sort);
			else params.delete('sorting');
			params.set('page', '1');
		});

	// Keeps the current rows on screen (dimmed) while the next page or filter loads
	const current = latest(() => paginatedResponse);
	const paginationData = $derived(current.value?.pagination ?? { total: 0, page: 1, perPage: 15 });

	const perPageOptions = [15, 25, 50, 100];
	const perPageItems = $derived(
		[...new Set([...perPageOptions, paginationData.perPage])]
			.filter((n) => n > 0)
			.sort((x, y) => x - y)
			.map((n) => ({ value: String(n), label: String(n) }))
	);

	// Row the context menu is open for, with the cursor position it opened at
	let ctx: { row: T; x: number; y: number } | null = $state(null);
	let ctxWidth = $state(0);
	let ctxHeight = $state(0);
	let innerWidth = $state(0);
	let innerHeight = $state(0);

	const ctxLeft = $derived.by(() => Math.max(8, Math.min(ctx?.x ?? 0, innerWidth - ctxWidth - 8)));
	const ctxTop = $derived.by(() => Math.max(8, Math.min(ctx?.y ?? 0, innerHeight - ctxHeight - 8)));

	function openContextMenu(e: MouseEvent, row: T) {
		if (!contextSnippet) return;
		e.preventDefault();
		ctx = { row, x: e.clientX, y: e.clientY };
	}

	$effect(() => {
		if (!ctx) return;
		const close = () => (ctx = null);
		const onKeyDown = (e: KeyboardEvent) => {
			if (e.key === 'Escape') close();
		};
		window.addEventListener('click', close);
		window.addEventListener('scroll', close, true);
		window.addEventListener('keydown', onKeyDown);
		return () => {
			window.removeEventListener('click', close);
			window.removeEventListener('scroll', close, true);
			window.removeEventListener('keydown', onKeyDown);
		};
	});

	function handleRowClick(e: MouseEvent, row: T) {
		if ((e.target as HTMLElement).closest('a, button')) return;
		const href = rowProps?.href?.(row);
		if (href && (e.metaKey || e.ctrlKey || e.shiftKey)) {
			window.open(href, '_blank', 'noopener');
		} else if (rowProps?.onClick) {
			rowProps.onClick(row);
		} else if (href && !e.altKey) {
			goto(href);
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
		paginationData.total === 0 ? 0 : (paginationData.page - 1) * paginationData.perPage + 1
	);
	const rangeEnd = $derived(
		Math.min(paginationData.page * paginationData.perPage, paginationData.total)
	);

	const handleSortChange = (column: TableColumn<T>) => {
		if (!column.sorting) return;
		// Cycle through the column's sort options, then back to unsorted
		const idx = sorting ? column.sorting.indexOf(sorting) : -1;
		sorting = idx === -1 ? column.sorting[0] : (column.sorting[idx + 1] ?? null);
		changeSort(sorting ?? '');
	};

	// Index of the expanded row, reset when the rows change
	let expanded = $derived.by<number | null>(() => {
		void current.value;
		return null;
	});
	const showChevron = $derived(!!rowProps?.expandedSnippet && !isExtraSmallLayout.current);
	const columnCount = $derived(columns.length + (showChevron ? 1 : 0));
	const interactive = $derived(
		!!(rowProps?.href || rowProps?.onClick || rowProps?.expandedSnippet)
	);
</script>

<svelte:window bind:innerWidth bind:innerHeight />

{#if contextSnippet && ctx}
	<div
		bind:clientWidth={ctxWidth}
		bind:clientHeight={ctxHeight}
		class={['fixed z-30', ctxWidth === 0 && 'invisible']}
		style="left: {ctxLeft}px; top: {ctxTop}px"
	>
		{@render contextSnippet(ctx.row)}
	</div>
{/if}

{#snippet skeletonRows()}
	{#each { length: Number(page.url.searchParams.get('per_page')) || perPageOptions[0] } as _, i (i)}
		<Table.Row>
			{#each columns as column, ci (ci)}
				<Table.Cell>
					<Skeleton class="h-4 w-full max-w-32 {column.align === 'right' ? 'ml-auto' : ''}" />
				</Table.Cell>
			{/each}
			{#if showChevron}<Table.Cell />{/if}
		</Table.Row>
	{/each}
{/snippet}

{#snippet cell(column: TableColumn<T>, row: T)}
	{#if column.renderSnippet}
		{@render column.renderSnippet(row)}
	{:else}
		{column.render?.(row) ?? ''}
	{/if}
{/snippet}

<Card padded={false}>
	<Table.Root class="table-fixed">
		<Table.Header>
			<Table.Row>
				{#each columns as column}
					<Table.Head align={column.align} class={column.width}>
						{#if column.sorting}
							{@const active = !!sorting && column.sorting.includes(sorting)}
							<button
								type="button"
								onclick={() => handleSortChange(column)}
								class={[
									'-mx-1 inline-flex max-w-full min-w-0 cursor-pointer items-center gap-1 px-1 py-0.5 [text-transform:inherit] transition-colors hover:text-foreground',
									active && 'text-foreground'
								]}
							>
								<span class="truncate" title={column.header}>{column.header}</span>
								{#if !active}
									<ChevronsUpDown class="size-3.5 shrink-0" />
								{:else if column.sorting.indexOf(sorting!) === 0}
									<ChevronDown class="size-3.5 shrink-0" />
								{:else}
									<ChevronUp class="size-3.5 shrink-0" />
								{/if}
							</button>
						{:else}
							<span class="block truncate">{column.header}</span>
						{/if}
					</Table.Head>
				{/each}
				{#if showChevron}
					<Table.Head class="w-12" />
				{/if}
			</Table.Row>
		</Table.Header>
		<Table.Body class={['transition-opacity', current.loading && 'opacity-60']}>
			{#if !current.value}
				{@render skeletonRows()}
			{:else}
				{@const response = current.value}
				{#each response.data as row, i}
					<Table.Row
						class={[
							'hover:bg-muted/50',
							interactive && 'cursor-pointer',
							expanded === i && 'bg-muted/50',
							typeof rowProps?.class === 'function' ? rowProps.class(row) : rowProps?.class
						]}
						onclick={(e) => {
							if (rowProps?.expandedSnippet) {
								expanded = expanded === i ? null : i;
							}
							handleRowClick(e, row);
						}}
						onauxclick={(e) => handleRowAuxClick(e, row)}
						oncontextmenu={(e) => openContextMenu(e, row)}
					>
						{#each columns as column, ci}
							<Table.Cell
								align={column.align}
								class={['overflow-hidden', !column.renderSnippet && 'truncate']}
							>
								{#if ci === 0 && rowProps?.href && !rowProps.onClick}
									<a href={rowProps.href(row)}>{@render cell(column, row)}</a>
								{:else}
									{@render cell(column, row)}
								{/if}
							</Table.Cell>
						{/each}
						{#if showChevron}
							<Table.Cell align="right" class="text-muted-foreground">
								{#if expanded === i}
									<ChevronUp class="ml-auto size-4" />
								{:else}
									<ChevronDown class="ml-auto size-4" />
								{/if}
							</Table.Cell>
						{/if}
					</Table.Row>
					{#if rowProps?.expandedSnippet && expanded === i}
						<Table.Row class="bg-muted/30">
							<Table.Cell colspan={columnCount} class="h-auto py-3">
								{@render rowProps.expandedSnippet(row)}
							</Table.Cell>
						</Table.Row>
					{/if}
				{/each}
				{#if response.data.length === 0}
					<Table.Row>
						<Table.Cell colspan={columnCount} class="h-24 text-center text-muted-foreground">
							{$_('no_results')}
						</Table.Cell>
					</Table.Row>
				{:else if response.pagination.total > response.pagination.perPage}
					{#each { length: response.pagination.perPage - response.data.length } as _}
						<tr aria-hidden="true" class="h-12"><td colspan={columnCount}></td></tr>
					{/each}
				{/if}
			{/if}
		</Table.Body>
	</Table.Root>

	<div
		class={[
			'flex items-center justify-center gap-4 border-t border-border px-3 py-2 md:justify-between',
			scrollable && 'bg-card lg:sticky lg:bottom-0 lg:z-10'
		]}
	>
		<p class="hidden text-sm text-muted-foreground md:block">
			{$_('admin_paginatedResponse.pagination.showing', {
				values: {
					start: rangeStart,
					end: rangeEnd,
					total: paginationData.total.toLocaleString()
				}
			})}
		</p>

		<Pagination.Root
			class="flex max-w-full items-center gap-1"
			count={paginationData.total}
			perPage={paginationData.perPage}
			page={paginationData.page}
			siblingCount={isSmallLayout.current ? 0 : 1}
			onPageChange={changePage}
		>
			{#snippet children({ pages })}
				<Pagination.PrevButton>
					{#snippet child({ props })}
						<Button variant="ghost" size="icon-sm" aria-label={$_('previous')} {...props}
							><ChevronLeft /></Button
						>
					{/snippet}
				</Pagination.PrevButton>
				{#each pages as page (page.key)}
					{#if page.type === 'ellipsis'}
						<span class="flex size-8 items-center justify-center text-sm text-muted-foreground">
							…
						</span>
					{:else}
						<Pagination.Page {page}>
							{#snippet child({ props })}
								<Button
									{...props}
									variant="ghost"
									size="icon-sm"
									class="font-normal text-muted-foreground tabular-nums data-selected:bg-muted data-selected:font-medium data-selected:text-foreground"
								>
									{page.value}
								</Button>
							{/snippet}
						</Pagination.Page>
					{/if}
				{/each}
				<Pagination.NextButton>
					{#snippet child({ props })}
						<Button variant="ghost" size="icon-sm" aria-label={$_('next')} {...props}
							><ChevronRight /></Button
						>
					{/snippet}
				</Pagination.NextButton>
			{/snippet}
		</Pagination.Root>

		<div class="hidden items-center gap-2 text-sm md:flex">
			<label for="per-page" class="text-muted-foreground">
				{$_('admin_paginatedResponse.pagination.show')}
			</label>
			<Select
				id="per-page"
				items={perPageItems}
				value={String(paginationData.perPage)}
				onValueChange={(v) => changePerPage(Number(v))}
				class="h-8 w-20"
			/>
		</div>
	</div>
</Card>
