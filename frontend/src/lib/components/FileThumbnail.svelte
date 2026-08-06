<script lang="ts">
	import { File as FileIcon, X } from '@lucide/svelte';
	import { Dialog } from 'bits-ui';
	import type { PdfDocumentObject, PdfEngine } from '@embedpdf/models';

	let {
		source,
		engine,
		class: className = 'h-16 w-12'
	}: { source: File | string; engine: PdfEngine | null; class?: string } = $props();

	const IMAGE_EXTENSION = /\.(png|jpe?g|gif|webp|bmp|avif|heic|heif)$/i;
	const PDF_EXTENSION = /\.pdf$/i;

	const name = $derived(
		typeof source === 'string'
			? decodeURIComponent(new URL(source).pathname.split('/').pop() ?? '')
			: source.name
	);
	const isImage = $derived(
		typeof source === 'string' ? IMAGE_EXTENSION.test(name) : source.type.startsWith('image/')
	);
	const isPdf = $derived(
		typeof source === 'string'
			? PDF_EXTENSION.test(name)
			: source.type === 'application/pdf' || PDF_EXTENSION.test(source.name)
	);

	let fileUrl = $state<string | null>(null);
	let pdfThumbUrl = $state<string | null>(null);
	let open = $state(false);

	const thumbSrc = $derived(isImage ? fileUrl : pdfThumbUrl);

	async function renderThumbnail(engine: PdfEngine, doc: PdfDocumentObject): Promise<string | null> {
		try {
			const blob = await engine
				.renderThumbnail(doc, doc.pages[0], { scaleFactor: 0.4 })
				.toPromise();
			return URL.createObjectURL(blob);
		} catch {
			return null;
		} finally {
			engine.closeDocument(doc);
		}
	}

	async function renderPdfFromUrl(engine: PdfEngine, url: string): Promise<string | null> {
		try {
			const doc = await engine.openDocumentUrl({ id: crypto.randomUUID(), url }).toPromise();
			return await renderThumbnail(engine, doc);
		} catch {
			return null;
		}
	}

	async function renderPdfFromFile(engine: PdfEngine, file: File): Promise<string | null> {
		try {
			const content = await file.arrayBuffer();
			const doc = await engine.openDocumentBuffer({ id: crypto.randomUUID(), content }).toPromise();
			return await renderThumbnail(engine, doc);
		} catch {
			return null;
		}
	}

	$effect(() => {
		let objectUrl: string | null = null;
		let pdfUrl: string | null = null;
		let cancelled = false;

		if (typeof source === 'string') {
			fileUrl = source;
		} else {
			objectUrl = URL.createObjectURL(source);
			fileUrl = objectUrl;
		}

		if (isPdf && engine) {
			const task =
				typeof source === 'string'
					? renderPdfFromUrl(engine, source)
					: renderPdfFromFile(engine, source);

			task.then((u) => {
				if (cancelled) {
					if (u) URL.revokeObjectURL(u);
					return;
				}
				pdfUrl = u;
				pdfThumbUrl = u;
			});
		}

		return () => {
			cancelled = true;
			fileUrl = null;
			pdfThumbUrl = null;
			if (objectUrl) URL.revokeObjectURL(objectUrl);
			if (pdfUrl) URL.revokeObjectURL(pdfUrl);
		};
	});
</script>

<Dialog.Root bind:open>
	<Dialog.Trigger
		type="button"
		class={[
			'flex cursor-pointer items-center justify-center transition-all hover:opacity-80',
			className
		]}
		title={name}
	>
		{#if thumbSrc}
			<img src={thumbSrc} alt={name} class="size-full object-cover" />
		{:else}
			<FileIcon class="m-auto" />
		{/if}
	</Dialog.Trigger>

	<Dialog.Portal>
		<Dialog.Overlay class="fixed inset-0 z-40 bg-black/70" />
		<Dialog.Content
			class="fixed top-1/2 left-1/2 z-50 flex max-h-[90vh] max-w-[90vw] -translate-x-1/2 -translate-y-1/2 flex-col shadow-2xl "
		>
			<div class="flex items-center justify-between gap-4 p-3">
				<Dialog.Close class="shrink-0 cursor-pointer transition-all hover:scale-110">
					<X />
				</Dialog.Close>
			</div>

			{#if isImage && fileUrl}
				<img src={fileUrl} alt={name} class="max-h-[80vh] max-w-[85vw] object-contain p-3 pt-0" />
			{:else if isPdf && fileUrl}
				<iframe src={fileUrl} title={name} class="h-[80vh] w-[85vw] border-0"></iframe>
			{/if}
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
