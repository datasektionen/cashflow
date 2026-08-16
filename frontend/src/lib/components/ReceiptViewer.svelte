<!--
@component
Receipt viewer. Renders PDF sources with embedPdf's headless viewer (document
manager, render, interaction manager and selection plugins), giving each PDF
page its own tile with real, selectable text, and uses plain <img> for image
receipts. Both kinds share the same grid/rotate/expand UI. Accepts one or
more url sources, of either kind, mixed or not.
-->
<script lang="ts">
	import { RotateCcw, RotateCw, Expand, X, ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { SvelteMap } from 'svelte/reactivity';
	import { createPluginRegistration } from '@embedpdf/core';
	import { EmbedPDF } from '@embedpdf/core/svelte';
	import { usePdfiumEngine } from '@embedpdf/engines/svelte';
	import { DocumentManagerPluginPackage } from '@embedpdf/plugin-document-manager';
	import { DocumentContent } from '@embedpdf/plugin-document-manager/svelte';
	import { RenderPluginPackage } from '@embedpdf/plugin-render';
	import { InteractionManagerPluginPackage } from '@embedpdf/plugin-interaction-manager';
	import { SelectionPluginPackage } from '@embedpdf/plugin-selection/svelte';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import RegisterPageCount from '$lib/components/RegisterPageCount.svelte';
	import CopySelection from '$lib/components/CopySelection.svelte';
	import PdfPage from '$lib/components/PdfPage.svelte';

	export type ReceiptViewerProps = {
		source: string[] | string;
	};

	const { source }: ReceiptViewerProps = $props();

	let sources: string[] = $derived(typeof source == 'string' ? [source] : source);

	const IMAGE_EXTENSION = /\.(png|jpe?g|gif|webp|bmp|avif|heic|heif)$/i;

	function isImage(url: string): boolean {
		return IMAGE_EXTENSION.test(new URL(url).pathname);
	}

	const pdfium = usePdfiumEngine();

	const pdfPlugins = (url: string) => [
		createPluginRegistration(DocumentManagerPluginPackage, {
			initialDocuments: [{ url, autoActivate: true }]
		}),
		createPluginRegistration(RenderPluginPackage),
		createPluginRegistration(InteractionManagerPluginPackage),
		createPluginRegistration(SelectionPluginPackage)
	];

	// A "page" for images (pageIndex is always null); one item per PDF page for PDFs.
	type Item = { url: string; pageIndex: number | null };

	function keyOf(item: Item): string {
		return item.pageIndex === null ? item.url : `${item.url}#${item.pageIndex}`;
	}

	let pageCounts: SvelteMap<string, number> = $state(new SvelteMap());

	function registerPageCount(url: string, count: number) {
		if (pageCounts.get(url) !== count) pageCounts.set(url, count);
		return count;
	}

	let items: Item[] = $derived(
		sources.flatMap((url): Item[] =>
			isImage(url)
				? [{ url, pageIndex: null }]
				: Array.from({ length: pageCounts.get(url) ?? 0 }, (_, pageIndex) => ({ url, pageIndex }))
		)
	);

	let enlarged: Item | null = $state(null);
	let rotationMap: SvelteMap<string, number> = $state(new SvelteMap<string, number>());

	const handleRotation = (item: Item, amount: number) => {
		const key = keyOf(item);
		const old = rotationMap.get(key);
		const newRotation = old ? old + amount : amount;
		rotationMap.set(key, newRotation);
	};

	function indexOfItem(item: Item): number {
		return items.findIndex((it) => it.url === item.url && it.pageIndex === item.pageIndex);
	}

	const getPrevious = (item: Item): Item => {
		const i = indexOfItem(item);
		return items[Math.max(i - 1, 0)];
	};
	const getNext = (item: Item): Item => {
		const i = indexOfItem(item);
		return items[Math.min(i + 1, items.length - 1)];
	};
</script>

{#snippet tileToolbar(item: Item)}
	<div
		class={[
			'absolute top-2 right-2 z-10 flex items-center gap-1',
			'bg-black/60 p-1 text-white shadow-lg ring-1 ring-white/10 backdrop-blur-sm',
			'transition-opacity md:opacity-0 md:group-hover:opacity-100'
		]}
	>
		<button
			onclick={() => handleRotation(item, -90)}
			class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
		>
			<RotateCcw class="size-4" />
		</button>
		<button
			onclick={() => handleRotation(item, 90)}
			class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
		>
			<RotateCw class="size-4" />
		</button>
		<button
			onclick={() => {
				enlarged = item;
			}}
			class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
		>
			<Expand class="size-4" />
		</button>
	</div>
{/snippet}

{#snippet pdfPageLoading()}
	<div
		class="flex aspect-square w-full shrink-0 items-center justify-center bg-black/5 text-base-subtle dark:text-dark-base-subtle"
	>
		<CashSpinner />
	</div>
{/snippet}

{#snippet pdfPageError(message: string)}
	<div
		class="flex aspect-square w-full shrink-0 items-center justify-center bg-black/5 text-sm text-red-500 dark:text-red-400"
	>
		{message}
	</div>
{/snippet}

{#snippet pdfGridPages(url: string)}
	{#if !pdfium.engine}
		{@render pdfPageLoading()}
	{:else}
		<EmbedPDF engine={pdfium.engine} plugins={pdfPlugins(url)}>
			{#snippet children({ activeDocumentId })}
				{#if activeDocumentId}
					<DocumentContent documentId={activeDocumentId}>
						{#snippet children(documentContent)}
							{#if documentContent.isLoading}
								{@render pdfPageLoading()}
							{:else if documentContent.isError}
								{@render pdfPageError('Failed to load PDF')}
							{:else if documentContent.isLoaded}
								{@const pageCount = documentContent.documentState.document?.pageCount ?? 0}
								<RegisterPageCount {url} count={pageCount} onRegister={registerPageCount} />
								<CopySelection documentId={activeDocumentId} />
								{@const pageIndexes = Array.from({ length: pageCount }, (_, i) => i)}
								{#each pageIndexes as pageIndex}
									{@const item = { url, pageIndex }}
									{@const size = documentContent.documentState.document?.pages[pageIndex]?.size}
									<div
										class="group relative flex aspect-square w-full shrink-0 items-center justify-center overflow-hidden"
									>
										<div
											class="h-full w-full"
											style="transform: rotate({rotationMap.get(keyOf(item)) ?? 0}deg)"
										>
											{#if size}
												<PdfPage documentId={activeDocumentId} {pageIndex} {size} />
											{/if}
										</div>
										{@render tileToolbar(item)}
									</div>
									{#if size && enlarged?.url === url && enlarged.pageIndex === pageIndex}
										<div
											class="fixed top-1/2 left-1/2 z-51 mx-auto flex h-[85vh] w-full max-w-3xl -translate-x-1/2 -translate-y-1/2 items-center justify-center"
										>
											<div
												class="h-full w-full"
												style="transform: rotate({rotationMap.get(keyOf(item)) ?? 0}deg)"
											>
												<PdfPage documentId={activeDocumentId} {pageIndex} {size} />
											</div>
										</div>
									{/if}
								{/each}
							{/if}
						{/snippet}
					</DocumentContent>
				{/if}
			{/snippet}
		</EmbedPDF>
	{/if}
{/snippet}

<div class="relative flex h-full w-full flex-col gap-4 overflow-auto border-0">
	{#each sources as url (url)}
		{#if isImage(url)}
			{@const item = { url, pageIndex: null }}
			<div
				class="group relative flex aspect-square w-full shrink-0 items-center justify-center overflow-hidden"
			>
				<div
					class="h-full w-full"
					style="transform: rotate({rotationMap.get(keyOf(item)) ?? 0}deg)"
				>
					<img src={url} alt="Receipt" class="h-full w-full object-contain" />
				</div>
				{@render tileToolbar(item)}
			</div>
		{:else}
			{@render pdfGridPages(url)}
		{/if}
	{/each}
</div>

<!-- Expanded overlay -->
<div
	role="button"
	tabindex="-1"
	aria-label="Close preview"
	class={[
		enlarged ? 'flex' : 'hidden',
		'fixed top-0 left-0 z-50 size-full bg-black/50 backdrop-blur-sm transition-all'
	]}
	onclick={() => {
		enlarged = null;
	}}
	onkeydown={(e) => {
		if (e.key === 'Escape' || e.key === 'Enter') enlarged = null;
	}}
></div>
<div
	class={[
		enlarged ? 'flex flex-col' : 'hidden',
		'fixed top-1/2 left-1/2 z-51 mx-auto max-h-screen w-full max-w-3xl -translate-x-1/2 -translate-y-1/2 gap-y-8 overflow-y-auto py-8'
	]}
>
	<div
		class="w-full"
		style="transform: rotate({rotationMap.get(enlarged ? keyOf(enlarged) : '') ?? 0}deg)"
	>
		{#if enlarged?.pageIndex === null}
			<img src={enlarged.url} alt="Enlarged receipt" class="w-full" />
		{/if}
	</div>
</div>

{#if enlarged}
	<div
		class={[
			'fixed bottom-0 left-1/2 z-52 grid -translate-x-1/2 grid-cols-3 items-center gap-1 md:bottom-2',
			'w-full md:w-120',
			'bg-black/60 p-1 text-white shadow-lg ring-1 ring-white/10 backdrop-blur-sm'
		]}
	>
		<div class="flex items-center gap-1 justify-self-start">
			<button
				onclick={() => handleRotation(enlarged!, -90)}
				class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
			>
				<RotateCcw class="size-6" />
			</button>
			<button
				onclick={() => handleRotation(enlarged!, 90)}
				class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
			>
				<RotateCw class="size-6" />
			</button>
		</div>

		<div class="flex items-center gap-1 justify-self-center">
			<button
				disabled={indexOfItem(enlarged!) === 0}
				onclick={() => {
					enlarged = getPrevious(enlarged!);
				}}
				class="cursor-pointer p-1.5 transition-colors hover:bg-white/20 disabled:cursor-default disabled:opacity-40 disabled:hover:bg-transparent"
			>
				<ChevronLeft class="size-6" />
			</button>
			<button
				disabled={indexOfItem(enlarged!) === items.length - 1}
				onclick={() => {
					enlarged = getNext(enlarged!);
				}}
				class="cursor-pointer p-1.5 transition-colors hover:bg-white/20 disabled:cursor-default disabled:opacity-40 disabled:hover:bg-transparent"
			>
				<ChevronRight class="size-6" />
			</button>
		</div>

		<div class="flex items-center justify-self-end">
			<button
				onclick={() => {
					enlarged = null;
				}}
				class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
			>
				<X class="size-6" />
			</button>
		</div>
	</div>
{/if}
