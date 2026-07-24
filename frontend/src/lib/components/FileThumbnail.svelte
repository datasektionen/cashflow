<script lang="ts">
	import { File as FileIcon, X } from '@lucide/svelte';
	import { Dialog } from 'bits-ui';
	import type { PdfEngine } from '@embedpdf/models';

	let {
		file,
		engine,
		class: className = 'h-16 w-12'
	}: { file: File; engine: PdfEngine | null; class?: string } = $props();

	const isImage = $derived(file.type.startsWith('image/'));
	const isPdf = $derived(file.type === 'application/pdf' || /\.pdf$/i.test(file.name));

	let fileUrl = $state<string | null>(null);
	let pdfThumbUrl = $state<string | null>(null);
	let open = $state(false);

	const thumbSrc = $derived(isImage ? fileUrl : pdfThumbUrl);

	async function renderPdf(engine: PdfEngine, file: File): Promise<string | null> {
		try {
			const content = await file.arrayBuffer();
			const doc = await engine.openDocumentBuffer({ id: crypto.randomUUID(), content }).toPromise();
			try {
				const blob = await engine
					.renderThumbnail(doc, doc.pages[0], { scaleFactor: 0.4 })
					.toPromise();
				return URL.createObjectURL(blob);
			} finally {
				engine.closeDocument(doc);
			}
		} catch {
			return null;
		}
	}

	$effect(() => {
		const objectUrl = URL.createObjectURL(file);
		fileUrl = objectUrl;

		let pdfUrl: string | null = null;
		let cancelled = false;

		if (isPdf && engine) {
			renderPdf(engine, file).then((u) => {
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
			URL.revokeObjectURL(objectUrl);
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
		title={file.name}
	>
		{#if thumbSrc}
			<img src={thumbSrc} alt={file.name} class="size-full object-cover" />
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
				<img
					src={fileUrl}
					alt={file.name}
					class="max-h-[80vh] max-w-[85vw] object-contain p-3 pt-0"
				/>
			{:else if isPdf && fileUrl}
				<iframe src={fileUrl} title={file.name} class="h-[80vh] w-[85vw] border-0"></iframe>
			{/if}
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
