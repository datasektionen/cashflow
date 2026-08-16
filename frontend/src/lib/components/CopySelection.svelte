<!--
@component
Wires Ctrl/Cmd+C to the selection plugin's copyToClipboard. The plugin only
exposes a `copyToClipboard()` method and an auto-mounted listener that writes
whatever it's given to the clipboard — nothing calls that method on its own,
since our PDF "text" isn't real DOM-selectable text, so the browser's native
copy shortcut has nothing to hook into without this.
-->
<script lang="ts">
	import { useSelectionCapability } from '@embedpdf/plugin-selection/svelte';

	export type CopySelectionProps = {
		documentId: string;
	};

	const { documentId }: CopySelectionProps = $props();

	const selection = useSelectionCapability();

	$effect(() => {
		function onKeydown(event: KeyboardEvent) {
			if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 'c') return;
			const provides = selection.provides;
			if (!provides?.getState(documentId).selection) return;
			provides.copyToClipboard(documentId);
		}

		window.addEventListener('keydown', onKeydown);
		return () => window.removeEventListener('keydown', onKeydown);
	});
</script>
