<!--
@component
Receipt viewer. Renders image receipts in a rotate/expand-capable grid;
PDF receipts are handed off to @embedpdf/snippet's self-contained reader
(own toolbar/zoom/rotate), one independent instance per file. Accepts one
or more url sources, of either kind, mixed or not.
-->
<script lang="ts">
	import { RotateCcw, RotateCw, Expand, X, ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { SvelteMap } from 'svelte/reactivity';
	import PdfSnippetViewer from '$lib/components/PdfSnippetViewer.svelte';

	export type ReceiptViewerProps = {
		source: string[] | string;
	};

	const { source }: ReceiptViewerProps = $props();

	let sources: string[] = $derived(typeof source == 'string' ? [source] : source);

	const IMAGE_EXTENSION = /\.(png|jpe?g|gif|webp|bmp|avif|heic|heif)$/i;

	function isImage(url: string): boolean {
		return IMAGE_EXTENSION.test(new URL(url).pathname);
	}

	let images: string[] = $derived(sources.filter(isImage));

	let enlarged: string | null = $state(null);
	let rotationMap: SvelteMap<string, number> = $state(new SvelteMap<string, number>());

	const handleRotation = (url: string, amount: number) => {
		const old = rotationMap.get(url);
		const newRotation = old ? old + amount : amount;
		rotationMap.set(url, newRotation);
	};

	function indexOfImage(url: string): number {
		return images.indexOf(url);
	}

	const getPrevious = (url: string): string => {
		const i = indexOfImage(url);
		return images[Math.max(i - 1, 0)];
	};
	const getNext = (url: string): string => {
		const i = indexOfImage(url);
		return images[Math.min(i + 1, images.length - 1)];
	};
</script>

{#snippet tileToolbar(url: string)}
	<div
		class={[
			'absolute top-2 right-2 z-10 flex items-center gap-1',
			'bg-black/60 p-1 text-white shadow-lg ring-1 ring-white/10 backdrop-blur-sm',
			'transition-opacity md:opacity-0 md:group-hover:opacity-100'
		]}
	>
		<button
			onclick={() => handleRotation(url, -90)}
			class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
		>
			<RotateCcw class="size-4" />
		</button>
		<button
			onclick={() => handleRotation(url, 90)}
			class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
		>
			<RotateCw class="size-4" />
		</button>
		<button
			onclick={() => {
				enlarged = url;
			}}
			class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
		>
			<Expand class="size-4" />
		</button>
	</div>
{/snippet}

<div class="relative flex h-full w-full flex-col gap-4 overflow-auto border-0">
	{#each sources as url (url)}
		{#if isImage(url)}
			<div
				class="group relative flex aspect-square w-full shrink-0 items-center justify-center overflow-hidden"
			>
				<div class="h-full w-full" style="transform: rotate({rotationMap.get(url) ?? 0}deg)">
					<img src={url} alt="Receipt" class="h-full w-full object-contain" />
				</div>
				{@render tileToolbar(url)}
			</div>
		{:else}
			<PdfSnippetViewer {url} />
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
	<div class="w-full" style="transform: rotate({rotationMap.get(enlarged ?? '') ?? 0}deg)">
		{#if enlarged}
			<img src={enlarged} alt="Enlarged receipt" class="w-full" />
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
				disabled={indexOfImage(enlarged!) === 0}
				onclick={() => {
					enlarged = getPrevious(enlarged!);
				}}
				class="cursor-pointer p-1.5 transition-colors hover:bg-white/20 disabled:cursor-default disabled:opacity-40 disabled:hover:bg-transparent"
			>
				<ChevronLeft class="size-6" />
			</button>
			<button
				disabled={indexOfImage(enlarged!) === images.length - 1}
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
