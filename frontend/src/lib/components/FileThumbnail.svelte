<script lang="ts">
	import { File as FileIcon } from '@lucide/svelte';
	import { fileName, isImageName } from '#lib/files.ts';
	import { pdfThumbnail, releasePdfThumbnail } from '#lib/pdfThumbnail.ts';
	import FileLightbox from './FileLightbox.svelte';

	let { source, class: className = 'h-16 w-12' }: { source: File | string; class?: string } =
		$props();

	const name = $derived(typeof source === 'string' ? fileName(source) : source.name);
	const isImage = $derived(
		typeof source === 'string' ? isImageName(name) : source.type.startsWith('image/')
	);
	const isPdf = $derived(
		/\.pdf$/i.test(name) || (typeof source !== 'string' && source.type === 'application/pdf')
	);

	const fileUrl = $derived(typeof source === 'string' ? source : URL.createObjectURL(source));
	$effect(() => {
		const current = source;
		const url = fileUrl;
		return () => {
			if (typeof current === 'string') return;
			URL.revokeObjectURL(url);
			releasePdfThumbnail(current);
		};
	});

	const pdfThumb = $derived(isPdf ? pdfThumbnail(source) : Promise.resolve(null));
	let open = $state(false);
</script>

<button
	type="button"
	tabindex="-1"
	onclick={() => (open = true)}
	class={[
		'flex cursor-pointer items-center justify-center overflow-hidden border border-border bg-muted text-muted-foreground transition-opacity hover:opacity-80',
		className
	]}
	title={name}
>
	{#if isImage}
		<img src={fileUrl} alt={name} class="size-full object-cover" />
	{:else}
		{#await pdfThumb then src}
			{#if src}
				<img {src} alt={name} class="size-full object-cover object-top" />
			{:else}
				<FileIcon class="m-auto size-5" />
			{/if}
		{/await}
	{/if}
</button>

{#if open}
	<FileLightbox files={[{ url: fileUrl, name, image: isImage }]} bind:open />
{/if}
