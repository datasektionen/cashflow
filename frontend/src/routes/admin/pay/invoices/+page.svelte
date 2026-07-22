<script lang="ts">
	import type { PageProps } from './$types';
	import type { Invoice } from '$lib/api/types';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import type { TableColumn } from '$lib/components/types';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { _, locale } from 'svelte-i18n';
	import UserLink from '$lib/components/UserLink.svelte';
	import InvoicePreview from './InvoicePreview.svelte';
	import { ScrollArea } from 'bits-ui';

	let { data }: PageProps = $props();

	let loading = $state(false);

	function total(invoice: Invoice): number {
		return invoice.parts.reduce((sum, part) => sum + parseFloat(part.amount), 0);
	}

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});

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

	let preview: Invoice | null = $state(null);

	function handleRowClick(invoice: Invoice) {
		if (window.matchMedia('(min-width: 1024px)').matches) {
			preview = invoice;
		} else {
			goto(`/admin/invoices/${invoice.id}`);
		}
	}

	const columns: TableColumn<Invoice>[] = [
		{
			id: 'invoice',
			header: $_('admin_pay.columns.invoice'),
			renderSnippet: invoiceCell,
			width: ''
		},
		{
			id: 'due_date',
			header: $_('admin_pay.columns.due_date'),
			renderSnippet: dueDateCell,
			width: 'w-32'
		},
		{
			id: 'total',
			header: $_('admin_pay.columns.total'),
			renderSnippet: totalCell,
			width: 'w-32'
		}
	];
</script>

{#snippet invoiceCell(invoice: Invoice)}
	<div class="flex min-w-0 flex-col gap-y-1">
		<span class="min-w-0 truncate font-medium">{invoice.description}</span>
		<span class="text-xs text-base-subtle dark:text-dark-base-subtle">
			<UserLink user={invoice.owner} />
		</span>
	</div>
{/snippet}

{#snippet dueDateCell(invoice: Invoice)}
	<span class="text-base-subtle tabular-nums dark:text-dark-base-subtle">
		{invoice.due_date ? new Date(invoice.due_date).toLocaleDateString($locale ?? 'sv-SE') : '–'}
	</span>
{/snippet}

{#snippet totalCell(invoice: Invoice)}
	<span class="font-semibold tabular-nums">{fmt.format(total(invoice))} kr</span>
{/snippet}

<div class="flex flex-col gap-6 lg:h-[calc(100dvh-10rem)] lg:flex-row lg:overflow-hidden">
	<div class="min-w-0 flex-1 lg:min-h-0 lg:max-w-4xl lg:overflow-y-auto">
		<PaginatedTable
			paginatedResponse={data.invoices}
			{columns}
			onPageChange={handlePageChange}
			onPerPageChange={handlePerPageChange}
			{loading}
			scrollable
			rowProps={{
				onClick: handleRowClick,
				class: (invoice: Invoice) =>
					preview && invoice.id === preview.id
						? 'cursor-pointer bg-base-200 dark:bg-dark-base-200'
						: 'cursor-pointer'
			}}
		/>
		{#if data.invoices.data.length === 0}
			<p class="p-8 text-center text-sm text-base-subtle dark:text-dark-base-subtle">
				{$_('admin_pay.empty')}
			</p>
		{/if}
	</div>

	<div class="hidden min-h-0 flex-1 lg:block lg:max-w-2xl">
		<ScrollArea.Root class="relative h-full w-full overflow-hidden">
			<ScrollArea.Viewport class="h-full w-full">
				<div class="px-8 pb-8">
					{#if !preview}
						<div class="flex h-full items-center justify-center py-24">
							<p class="text-sm text-base-subtle dark:text-dark-base-subtle">
								{$_('admin_pay.preview.empty')}
							</p>
						</div>
					{:else}
						{#key preview.id}
							<InvoicePreview invoiceId={preview.id} onPaid={() => (preview = null)} />
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
