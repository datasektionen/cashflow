<!--
@component
Receipt viewer. Renders PDFs with embedPdf's standard viewer (not ideal, but
works) and falls back to plain <img> for image receipts, which embedPdf can't
render. Accepts one or more url sources, of either kind, mixed or not.
-->
<script lang="ts">
	import { RotateCcw, RotateCw, Expand, X, ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { usePdfiumEngine } from '@embedpdf/engines/svelte';
	import { SvelteMap } from 'svelte/reactivity';
	import type { PdfEngine } from '@embedpdf/models';

	export type ReceiptViewerProps = {
		source: string[] | string;
	};

	const { source }: ReceiptViewerProps = $props();

	let sources: string[] = $derived(typeof source == 'string' ? [source] : source);

	const IMAGE_EXTENSION = /\.(png|jpe?g|gif|webp|bmp|avif|heic|heif)$/i;

	function isImage(url: string): boolean {
		return IMAGE_EXTENSION.test(new URL(url).pathname);
	}

	let imageSources: string[] = $derived(sources.filter(isImage));
	let pdfSources: string[] = $derived(sources.filter((s) => !isImage(s)));

	const pdfium = usePdfiumEngine();

	let pdfImageSources = $state<string[]>([]);

	let enlarged: string | null = $state(null);
	let rotationMap: SvelteMap<string, number> = $state(new SvelteMap<string, number>());

	let allSources: string[] = $derived([...imageSources, ...pdfImageSources]);

	const renderPdf = async (engine: PdfEngine, src: string): Promise<string[]> => {
		const doc = await engine.openDocumentUrl({ id: crypto.randomUUID(), url: src }).toPromise();
		const images = await Promise.all(
			doc.pages.map((page) => engine.renderPage(doc, page, { scaleFactor: 2 }).toPromise())
		);
		return images.map((img) => URL.createObjectURL(img));
	};

	$effect(() => {
		const engine = pdfium.engine;
		if (!engine || pdfSources.length === 0) return;

		let cancelled = false;
		let created: string[] = [];

		Promise.all(pdfSources.map((src) => renderPdf(engine, src))).then((results) => {
			created = results.flat();
			if (cancelled) {
				created.forEach((url) => URL.revokeObjectURL(url));
				return;
			}
			pdfImageSources = created;
		});

		return () => {
			cancelled = true;
			pdfImageSources = [];
			created.forEach((url) => URL.revokeObjectURL(url));
		};
	});

	const handleRotation = (src: string, amount: number) => {
		const old = rotationMap.get(src);
		const newRotation = old ? old + amount : amount;
		rotationMap.set(src, newRotation);
	};

	const getPrevious = (src: string) => {
		const i = allSources.indexOf(src);
		return allSources[Math.max(i - 1, 0)];
	};
	const getNext = (src: string) => {
		const i = allSources.indexOf(src);
		return allSources[Math.min(i + 1, allSources.length - 1)];
	};
</script>

<div class="relative flex h-full w-full flex-col gap-4 overflow-auto border-0">
	{#each allSources as src, i (src)}
		<div
			class="group relative flex aspect-square w-full shrink-0 items-center justify-center overflow-hidden"
		>
			<img
				{src}
				alt={(i + 1).toString()}
				class="h-full w-full object-contain"
				style="transform: rotate({rotationMap.get(src) ?? 0}deg)"
			/>

			<!-- Toolbar -->
			<div
				class={[
					'absolute top-2 right-2 z-10 flex items-center gap-1',
					'bg-black/60 p-1 text-white shadow-lg ring-1 ring-white/10 backdrop-blur-sm',
					'transition-opacity md:opacity-0 md:group-hover:opacity-100'
				]}
			>
				<button
					onclick={() => handleRotation(src, -90)}
					class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
				>
					<RotateCcw class="size-4" />
				</button>
				<button
					onclick={() => handleRotation(src, 90)}
					class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
				>
					<RotateCw class="size-4" />
				</button>
				<button
					onclick={() => {
						enlarged = src;
					}}
					class="cursor-pointer p-1.5 transition-colors hover:bg-white/20"
				>
					<Expand class="size-4" />
				</button>
			</div>
		</div>
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
		'fixed top-0 top-1/2 left-1/2 z-51 mx-auto max-h-screen w-full max-w-3xl -translate-x-1/2 -translate-y-1/2 gap-y-8 overflow-y-auto py-8'
	]}
>
	<img
		src={enlarged}
		alt="Enlarged receipt"
		class="w-full"
		style="transform: rotate({rotationMap.get(enlarged ?? '') ?? 0}deg)"
	/>
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
				disabled={allSources.indexOf(enlarged!) === 0}
				onclick={() => {
					enlarged = getPrevious(enlarged!);
				}}
				class="cursor-pointer p-1.5 transition-colors hover:bg-white/20 disabled:cursor-default disabled:opacity-40 disabled:hover:bg-transparent"
			>
				<ChevronLeft class="size-6" />
			</button>
			<button
				disabled={allSources.indexOf(enlarged!) === allSources.length - 1}
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
