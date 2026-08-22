<!--
@component
Renders one PDF using @embedpdf/snippet's self-contained reader (own
toolbar, zoom, rotate, search) instead of our hand-rolled EmbedPDF plugin
composition. Swapped in because running multiple independent `<EmbedPDF>`
plugin-registry instances (one per file, our own composition) turned out
to be an edge case the library doesn't handle reliably — content bled
between tiles, then engine load contention caused intermittent blank
tiles, then concurrent per-page renders within one file only showed the
last page. @embedpdf/snippet is built and tested specifically for
embedding multiple standalone viewer instances on one page.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import EmbedPDF from '@embedpdf/snippet';

	let { url }: { url: string } = $props();

	let container: HTMLDivElement;

	onMount(() => {
		EmbedPDF.init({
			type: 'container',
			target: container,
			src: url
		});
	});
</script>

<div bind:this={container} class="h-[36rem] w-full shrink-0"></div>
