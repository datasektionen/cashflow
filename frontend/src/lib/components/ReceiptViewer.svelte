<!--
@component
Receipt viewer. Renders PDFs with embedPdf's standard viewer (not ideal, but
works) and falls back to plain <img> for image receipts, which embedPdf can't
render. Accepts one or more url sources, of either kind, mixed or not.
-->
<script lang="ts">
	import { ScrollStrategy, ZoomMode } from '@embedpdf/snippet';
	import { PDFViewer } from '@embedpdf/svelte-pdf-viewer';
	import { locale } from 'svelte-i18n';

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
</script>

<div class="flex h-full w-full flex-col gap-4 overflow-auto">
	{#each imageSources as src, i (src)}
		<img {src} alt={(i + 1).toString()} class="w-full" />
	{/each}

	{#if pdfSources.length > 0}
		<PDFViewer
			config={{
				documentManager: {
					initialDocuments: pdfSources.map((s, i) => ({
						url: s,
						name: (i + 1).toString()
					}))
				},
				tabBar: pdfSources.length > 1 ? 'multiple' : 'never',
				theme: { preference: 'system' },
				disabledCategories: ['annotation', 'redaction', 'search'],
				zoom: { defaultZoomLevel: ZoomMode.FitWidth },
				scroll: { defaultStrategy: ScrollStrategy.Vertical },
				i18n: { defaultLocale: $locale ?? 'sv', fallbackLocale: 'en' }
			}}
			style="width: 100%; height: 100%"
		/>
	{/if}
</div>
