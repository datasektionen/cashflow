<script lang="ts">
	import { onMount } from 'svelte';
	import EmbedPDF, {
		type DocumentManagerPlugin,
		type EmbedPdfContainer,
		type InteractionManagerPlugin,
		type UIPlugin
	} from '@embedpdf/snippet';
	import { pdfiumWasmUrl } from '#lib/pdfium.ts';

	// Inline viewers sit inside a page: no toolbar, and touch scrolls the page
	type Props = { url: string; class: string; inline?: boolean };

	let { url, class: className, inline = false }: Props = $props();

	let container: HTMLDivElement;

	// Matches the tokens in app.css; the viewer renders in its own shadow root
	const light = {
		background: {
			app: '#f8fafc',
			surface: '#ffffff',
			surfaceAlt: '#f1f5f9',
			elevated: '#ffffff',
			overlay: 'rgba(0, 0, 0, 0.4)',
			input: '#ffffff'
		},
		foreground: {
			primary: '#111827',
			secondary: '#374151',
			muted: '#5b6574',
			disabled: '#9aa3b0',
			onAccent: '#ffffff'
		},
		border: { default: '#d3dae3', subtle: '#eef2f6', strong: '#848f9e' },
		accent: {
			primary: '#278032',
			primaryHover: '#216c2a',
			primaryActive: '#1a5221',
			primaryLight: '#e8f6ea',
			primaryForeground: '#ffffff'
		},
		interactive: {
			hover: '#f1f5f9',
			active: '#e2e8f0',
			selected: '#e8f6ea',
			focus: '#278032',
			focusRing: 'rgba(39, 128, 50, 0.35)'
		},
		state: {
			error: '#dc2626',
			errorLight: '#fef2f2',
			warning: '#d97706',
			warningLight: '#fffbeb',
			success: '#278032',
			successLight: '#e8f6ea',
			info: '#1e40af',
			infoLight: '#eff6ff'
		},
		scrollbar: { track: 'transparent', thumb: '#a7d3ac', thumbHover: '#278032' },
		tooltip: { background: '#111827', foreground: '#ffffff' }
	};

	const dark = {
		background: {
			app: '#1a1c20',
			surface: '#22252b',
			surfaceAlt: '#2b2f37',
			elevated: '#22252b',
			overlay: 'rgba(0, 0, 0, 0.6)',
			input: '#22252b'
		},
		foreground: {
			primary: '#e5e9f0',
			secondary: '#c3cad5',
			muted: '#9aa3b0',
			disabled: '#646d7c',
			onAccent: '#ffffff'
		},
		border: { default: '#373c46', subtle: '#2b2f37', strong: '#6b7381' },
		accent: {
			primary: '#278032',
			primaryHover: '#216c2a',
			primaryActive: '#1a5221',
			primaryLight: '#16301b',
			primaryForeground: '#ffffff'
		},
		interactive: {
			hover: '#2b2f37',
			active: '#343943',
			selected: '#16301b',
			focus: '#4dbf57',
			focusRing: 'rgba(77, 191, 87, 0.35)'
		},
		state: {
			error: '#dc2626',
			errorLight: '#3a1717',
			warning: '#f59e0b',
			warningLight: '#36260d',
			success: '#4dbf57',
			successLight: '#16301b',
			info: '#93c5fd',
			infoLight: '#172338'
		},
		scrollbar: { track: 'transparent', thumb: '#2c5233', thumbHover: '#4dbf57' },
		tooltip: { background: '#e5e9f0', foreground: '#1a1c20' }
	};

	const theme = () =>
		({
			preference: document.documentElement.classList.contains('dark') ? 'dark' : 'light',
			light,
			dark
		}) as const;

	// Hides the toolbar; on touch screens text selection gives way to scrolling the page
	async function makeInline(viewer: EmbedPdfContainer) {
		const registry = await viewer.registry;
		const ui = registry.getPlugin<UIPlugin>('ui')?.provides();
		const interaction = matchMedia('(pointer: coarse)').matches
			? registry.getPlugin<InteractionManagerPlugin>('interaction-manager')?.provides()
			: undefined;
		interaction?.registerMode({
			id: 'scroll',
			scope: 'page',
			exclusive: false,
			wantsRawTouch: false
		});
		registry
			.getPlugin<DocumentManagerPlugin>('document-manager')
			?.provides()
			.onDocumentOpened((doc) => {
				ui?.forDocument(doc.id).closeToolbarSlot('top', 'main');
				interaction?.forDocument(doc.id).activate('scroll');
			});
	}

	onMount(() => {
		const viewer = EmbedPDF.init({
			type: 'container',
			target: container,
			src: url,
			wasmUrl: pdfiumWasmUrl(),
			theme: theme(),
			pan: { defaultMode: inline ? 'never' : 'mobile' }
		});
		if (viewer && inline) makeInline(viewer);
		// Follow the app's theme toggle, which switches the class on <html>
		const observer = new MutationObserver(() => viewer?.setTheme(theme()));
		observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
		return () => observer.disconnect();
	});
</script>

<div bind:this={container} class={['w-full overflow-hidden', className]}></div>
