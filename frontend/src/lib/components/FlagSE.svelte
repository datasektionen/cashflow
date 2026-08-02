<script lang="ts">
	import type { ClassValue } from 'svelte/elements';

	// Swedish flag. Official 16:10 construction with the off-centre cross.
	let { class: className = 'size-5' }: { class?: ClassValue } = $props();
</script>

<svg viewBox="0 0 16 10" class={className} role="img" aria-label="Svenska">
	<rect width="16" height="10" fill="#006AA7" />
	<path d="M5 0h2v10H5z M0 4h16v2H0z" fill="#FECC00" />
</svg>
