<script lang="ts">
	import type { Snippet } from 'svelte';
	import { _ } from 'svelte-i18n';
	import { FileX, PanelRightOpen } from '@lucide/svelte';
	import { EmptyState } from '#lib/components/ui/index.ts';
	import { DEFAULT_PREFERENCES, getPreferences } from '#lib/preferences.svelte.ts';
	import ReceiptViewer from './ReceiptViewer.svelte';
	import type { ViewerFile } from './FileLightbox.svelte';

	// Content with its receipts in a resizable, sticky column on the right; null files hides the column
	type Props = {
		files: (string | ViewerFile)[] | null;
		// Closing hides the column (remembered) unless the caller handles it
		onclose?: () => void;
		// Above the receipts on phones, next to them on desktop
		header?: Snippet;
		children: Snippet;
	};

	let { files, onclose, header, children }: Props = $props();

	const DEFAULT_WIDTH = DEFAULT_PREFERENCES.receiptWidth;
	// Percent of the layout; 0 means hidden
	const prefs = getPreferences();
	const shown = $derived(!!files && (prefs.receiptWidth > 0 || !!onclose));
	const percent = $derived(prefs.receiptWidth || DEFAULT_WIDTH);

	let grid: HTMLDivElement;
	let dragging = $state(false);
	// Dragged far enough that letting go closes the column
	let closing = $state(false);

	function close() {
		if (onclose) onclose();
		else prefs.receiptWidth = 0;
	}

	// Follows the pointer from where it grabbed the handle; dropping the column nearly shut closes it
	function resize(e: PointerEvent) {
		const handle = e.currentTarget as HTMLElement;
		handle.setPointerCapture(e.pointerId);
		dragging = true;
		const start = { x: e.clientX, percent, width: grid.getBoundingClientRect().width };
		const move = (m: PointerEvent) => {
			const raw = start.percent + ((start.x - m.clientX) / start.width) * 100;
			prefs.receiptWidth = Math.min(70, Math.max(20, raw));
			closing = raw < 12;
		};
		handle.addEventListener('pointermove', move);
		handle.addEventListener(
			'lostpointercapture',
			() => {
				handle.removeEventListener('pointermove', move);
				if (closing) close();
				dragging = closing = false;
			},
			{ once: true }
		);
	}
</script>

<div
	bind:this={grid}
	style:--receipt-width="{percent}%"
	class={[
		'grid grid-cols-1 gap-6',
		shown && 'lg:grid-cols-[minmax(0,1fr)_var(--receipt-width)] lg:items-start',
		shown && header && 'lg:grid-rows-[auto_1fr]'
	]}
>
	{#if header}
		<div class="flex min-w-0 flex-col gap-6">{@render header()}</div>
	{/if}
	{#if files && shown}
		<aside
			class={[
				'relative flex h-[65dvh] flex-col border border-border bg-card transition-opacity lg:sticky lg:top-6 lg:col-start-2 lg:row-start-1 lg:h-[calc(100dvh-7rem)]',
				header && 'lg:row-span-2',
				closing && 'opacity-40'
			]}
		>
			<div
				role="separator"
				aria-orientation="vertical"
				aria-label={$_('resize')}
				onpointerdown={resize}
				ondblclick={() => (prefs.receiptWidth = DEFAULT_WIDTH)}
				class="group absolute inset-y-0 -left-5 hidden w-4 cursor-col-resize touch-none items-center justify-center lg:flex"
			>
				<span
					class={[
						'h-12 w-1 transition-colors group-hover:bg-primary',
						dragging ? 'bg-primary' : 'bg-border'
					]}
				></span>
			</div>
			{#if files.length > 0}
				<ReceiptViewer source={files} onclose={close} />
			{:else}
				<EmptyState icon={FileX} title={$_('expense_no_files')} class="flex-1 border-0" />
			{/if}
		</aside>
	{:else if files}
		<button
			type="button"
			aria-label={$_('show_receipt')}
			title={$_('show_receipt')}
			onclick={() => (prefs.receiptWidth = DEFAULT_WIDTH)}
			class="fixed top-1/2 right-0 z-20 flex -translate-y-1/2 cursor-pointer items-center border border-r-0 border-input bg-card p-2 text-muted-foreground shadow-md transition-colors hover:bg-muted hover:text-foreground [&_svg]:size-5"
		>
			<PanelRightOpen />
		</button>
	{/if}
	<div class="flex min-w-0 flex-col gap-6 lg:col-start-1">{@render children()}</div>
</div>
