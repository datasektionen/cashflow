<script lang="ts" module>
	export type ViewerFile = { url: string; name: string; image: boolean };
</script>

<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { zoomable } from '#lib/zoom.ts';
	import { Dialog } from 'bits-ui';
	import { SvelteMap } from 'svelte/reactivity';
	import { ChevronLeft, ChevronRight, ExternalLink, RotateCcw, RotateCw, X } from '@lucide/svelte';
	import PdfSnippetViewer from './PdfSnippetViewer.svelte';

	type Props = {
		files: ViewerFile[];
		index?: number;
		open?: boolean;
		rotation?: SvelteMap<string, number>;
	};

	let {
		files,
		index = $bindable(0),
		open = $bindable(false),
		rotation = new SvelteMap()
	}: Props = $props();

	const file = $derived(files[index]);
	let pdf = $state<HTMLElement | null>(null);
	const step = (by: number) => (index = (index + by + files.length) % files.length);
	const rotate = (by: number) => rotation.set(file.url, (rotation.get(file.url) ?? 0) + by);

	const tool =
		'inline-flex size-9 shrink-0 cursor-pointer items-center justify-center text-white/70 transition-colors hover:bg-white/10 hover:text-white [&_svg]:size-5';
	const arrow =
		'absolute top-1/2 inline-flex size-11 -translate-y-1/2 cursor-pointer items-center justify-center bg-white/10 text-white transition-colors hover:bg-white/20 [&_svg]:size-6';
</script>

<Dialog.Root bind:open>
	<Dialog.Portal>
		<Dialog.Overlay class="fixed inset-0 z-50 bg-neutral-950/95" />
		<Dialog.Content
			class="fixed inset-0 z-50 flex flex-col text-white outline-none"
			onkeydown={(e) => {
				if (pdf?.contains(e.target as Node)) return;
				if (e.key === 'ArrowLeft') step(-1);
				if (e.key === 'ArrowRight') step(1);
			}}
		>
			<div class="flex h-14 shrink-0 items-center gap-1 px-3">
				{#if files.length > 1}
					<span class="px-2 font-mono text-sm text-white/60">{index + 1} / {files.length}</span>
				{/if}
				<Dialog.Title class="min-w-0 flex-1 truncate px-2 text-sm font-medium">
					{file.name}
				</Dialog.Title>
				{#if file.image}
					<button
						type="button"
						class={tool}
						aria-label={$_('rotate_left')}
						onclick={() => rotate(-90)}
					>
						<RotateCcw />
					</button>
					<button
						type="button"
						class={tool}
						aria-label={$_('rotate_right')}
						onclick={() => rotate(90)}
					>
						<RotateCw />
					</button>
				{/if}
				<a
					class={tool}
					href={file.url}
					target="_blank"
					rel="noopener noreferrer"
					aria-label={$_('open_in_new_tab')}
				>
					<ExternalLink />
				</a>
				<Dialog.Close class={tool} aria-label={$_('close')}><X /></Dialog.Close>
			</div>

			<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
			<div
				class="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden px-4 pb-4 sm:px-20"
				onclick={(e) => e.target === e.currentTarget && (open = false)}
			>
				{#key file.url}
					{#if file.image}
						<img
							src={file.url}
							alt={file.name}
							class="max-h-full max-w-full object-contain transition-[rotate]"
							style:rotate="{rotation.get(file.url) ?? 0}deg"
							draggable="false"
							{@attach zoomable}
						/>
					{:else}
						<div bind:this={pdf} class="contents">
							<PdfSnippetViewer url={file.url} class="h-full max-w-5xl" />
						</div>
					{/if}
				{/key}
				{#if files.length > 1}
					<button
						type="button"
						class="{arrow} left-4"
						aria-label={$_('previous')}
						onclick={() => step(-1)}
					>
						<ChevronLeft />
					</button>
					<button
						type="button"
						class="{arrow} right-4"
						aria-label={$_('next')}
						onclick={() => step(1)}
					>
						<ChevronRight />
					</button>
				{/if}
			</div>
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
