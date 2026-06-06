<!--
@component
PDF-viewer for receipts. Currently uses embedPdfs standard viewer, which is not ideal.
Accepts one or more url sources.
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
</script>

<PDFViewer
	config={{
		documentManager: {
			initialDocuments: sources.map((s, i) => ({
				url: s,
				name: (i + 1).toString()
			}))
		},
		tabBar: sources.length > 1 ? 'multiple' : 'never',
		theme: { preference: 'system' },
		disabledCategories: ['annotation', 'redaction', 'search'],
		zoom: { defaultZoomLevel: ZoomMode.FitWidth },
		scroll: { defaultStrategy: ScrollStrategy.Vertical },
		i18n: { defaultLocale: $locale ?? 'sv', fallbackLocale: 'en' }
	}}
	style="width: 100%; height: 100%"
/>
