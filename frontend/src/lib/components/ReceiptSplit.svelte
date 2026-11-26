<script lang="ts">
	import type { Snippet } from 'svelte';
	import ReceiptLayout from './ReceiptLayout.svelte';

	// Shows an uploaded receipt next to the form so the parts can be typed off it
	let { file = $bindable(), children }: { file: File | null; children: Snippet } = $props();

	const url = $derived(file ? URL.createObjectURL(file) : null);
	$effect(() => {
		const current = url;
		return () => {
			if (current) URL.revokeObjectURL(current);
		};
	});
</script>

<ReceiptLayout
	files={file && url ? [{ url, name: file.name, image: file.type.startsWith('image/') }] : null}
	onclose={() => (file = null)}
>
	{@render children()}
</ReceiptLayout>
