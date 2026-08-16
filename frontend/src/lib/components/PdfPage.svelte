<!--
@component
Renders one PDF page at whatever scale exactly fills its container. This
can't be done with a fixed scale + CSS max-width/max-height clamp: embedPdf's
PagePointerProvider derives pointer-to-page coordinate math from the `scale`
prop alone, so if CSS later shrinks its box smaller than that scale implies,
clicks land at the wrong page position (selection drifts/over-extends). We
measure the real container instead, so the scale we pass always matches the
actual rendered size.
-->
<script lang="ts">
	import { PagePointerProvider } from '@embedpdf/plugin-interaction-manager/svelte';
	import { RenderLayer } from '@embedpdf/plugin-render/svelte';
	import { SelectionLayer } from '@embedpdf/plugin-selection/svelte';

	export type PdfPageProps = {
		documentId: string;
		pageIndex: number;
		size: { width: number; height: number };
	};

	const { documentId, pageIndex, size }: PdfPageProps = $props();

	let containerWidth: number = $state(0);
	let containerHeight: number = $state(0);

	let scale: number = $derived(
		containerWidth > 0 && containerHeight > 0
			? Math.min(containerWidth / size.width, containerHeight / size.height)
			: 0
	);
</script>

<div
	class="flex h-full w-full items-center justify-center"
	bind:clientWidth={containerWidth}
	bind:clientHeight={containerHeight}
>
	{#if scale > 0}
		<PagePointerProvider {documentId} {pageIndex} {scale}>
			<RenderLayer {documentId} {pageIndex} {scale} />
			<SelectionLayer {documentId} {pageIndex} {scale} />
		</PagePointerProvider>
	{/if}
</div>
