<script lang="ts">
	import type { ClassValue } from 'svelte/elements';

	// Union Jack, used to represent the English language toggle.
	let { class: className = 'size-5' }: { class?: ClassValue } = $props();
</script>

<svg viewBox="0 0 60 30" class={className} role="img" aria-label="English">
	<clipPath id="flag-en-round"><rect width="60" height="30" /></clipPath>
	<clipPath id="flag-en-tri">
		<path d="M30,15 h30 v15 z v15 h-30 z h-30 v-15 z v-15 h30 z" />
	</clipPath>
	<g clip-path="url(#flag-en-round)">
		<rect width="60" height="30" fill="#012169" />
		<path d="M0,0 L60,30 M60,0 L0,30" stroke="#fff" stroke-width="6" />
		<path
			d="M0,0 L60,30 M60,0 L0,30"
			clip-path="url(#flag-en-tri)"
			stroke="#C8102E"
			stroke-width="4"
		/>
		<path d="M30,0 v30 M0,15 h60" stroke="#fff" stroke-width="10" />
		<path d="M30,0 v30 M0,15 h60" stroke="#C8102E" stroke-width="6" />
	</g>
</svg>
