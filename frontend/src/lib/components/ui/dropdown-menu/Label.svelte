<script lang="ts">
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
</script>

<div class="px-2 py-1.5 text-xs font-medium text-muted-foreground">{@render children()}</div>
