<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { zoomable } from '#lib/zoom.ts';
	import {
		ChevronLeft,
		ChevronRight,
		FileText,
		Maximize2,
		RotateCcw,
		RotateCw,
		X
	} from '@lucide/svelte';
	import { SvelteMap } from 'svelte/reactivity';
	import { fileName, isImageName } from '#lib/files.ts';
	import { pdfThumbnail } from '#lib/pdfThumbnail.ts';
	import PdfSnippetViewer from './PdfSnippetViewer.svelte';
	import FileLightbox, { type ViewerFile } from './FileLightbox.svelte';

	// Shows one receipt at a time, filling its container
	type Props = { source: (string | ViewerFile)[]; onclose?: () => void };

	let { source, onclose }: Props = $props();

	const files = $derived(
		source.map((file) => {
			if (typeof file !== 'string') return file;
			const name = fileName(file);
			return { url: file, name, image: isImageName(name) };
		})
	);

	const rotation = new SvelteMap<string, number>();
	let open = $state(false);
	let index = $state(0);
	const current = $derived(Math.min(index, files.length - 1));
	const file = $derived(files[current]);

	const step = (by: number) => (index = (current + by + files.length) % files.length);
	const rotate = (by: number) => rotation.set(file.url, (rotation.get(file.url) ?? 0) + by);

	const tool =
		'inline-flex size-8 shrink-0 cursor-pointer items-center justify-center text-muted-foreground transition-colors hover:bg-muted hover:text-foreground [&_svg]:size-4';
</script>

<figure class="flex min-h-0 w-full flex-1 flex-col bg-card">
	<figcaption class="flex h-10 shrink-0 items-center gap-0.5 border-b border-border px-1">
		{#if files.length > 1}
			<button type="button" class={tool} aria-label={$_('previous')} onclick={() => step(-1)}>
				<ChevronLeft />
			</button>
			<span class="font-mono text-xs text-muted-foreground tabular-nums">
				{current + 1}/{files.length}
			</span>
			<button type="button" class={tool} aria-label={$_('next')} onclick={() => step(1)}>
				<ChevronRight />
			</button>
		{/if}
		<span class="min-w-0 flex-1 truncate px-2 text-xs text-muted-foreground">{file.name}</span>
		{#if file.image}
			<button type="button" class={tool} aria-label={$_('rotate_left')} onclick={() => rotate(-90)}>
				<RotateCcw />
			</button>
			<button type="button" class={tool} aria-label={$_('rotate_right')} onclick={() => rotate(90)}>
				<RotateCw />
			</button>
		{/if}
		<button type="button" class={tool} aria-label={$_('expand')} onclick={() => (open = true)}>
			<Maximize2 />
		</button>
		{#if onclose}
			<button type="button" class={tool} aria-label={$_('close')} onclick={onclose}>
				<X />
			</button>
		{/if}
	</figcaption>
	{#key file.url}
		{#if file.image}
			<div class="flex min-h-0 flex-1 items-center justify-center overflow-hidden bg-muted p-2">
				<img
					src={file.url}
					alt={file.name}
					class="size-full object-contain transition-[rotate]"
					style:rotate="{rotation.get(file.url) ?? 0}deg"
					draggable="false"
					{@attach zoomable}
				/>
			</div>
		{:else}
			<PdfSnippetViewer url={file.url} class="min-h-0 flex-1" inline />
		{/if}
	{/key}
	{#if files.length > 1}
		<div class="flex shrink-0 gap-2 overflow-x-auto border-t border-border p-2">
			<!-- Keyed by position: a claim can have the same file twice -->
			{#each files as f, i (i)}
				<button
					type="button"
					title={f.name}
					aria-label={f.name}
					aria-current={f === file || undefined}
					onclick={() => (index = i)}
					class={[
						'flex size-14 shrink-0 cursor-pointer items-center justify-center overflow-hidden border-2 bg-muted text-muted-foreground transition',
						f === file ? 'border-primary' : 'border-transparent opacity-60 hover:opacity-100'
					]}
				>
					{#if f.image}
						<img src={f.url} alt="" class="size-full object-cover object-top" />
					{:else}
						{#await pdfThumbnail(f.url)}
							<FileText class="size-6" />
						{:then src}
							{#if src}
								<img {src} alt="" class="size-full bg-white object-cover object-top" />
							{:else}
								<FileText class="size-6" />
							{/if}
						{/await}
					{/if}
				</button>
			{/each}
		</div>
	{/if}
</figure>

<FileLightbox {files} bind:index={() => current, (i) => (index = i)} bind:open {rotation} />
