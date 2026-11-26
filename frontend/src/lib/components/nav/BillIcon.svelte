<script lang="ts">
	let { class: className }: { class?: string } = $props();
	const id = $props.id();
</script>

<svg viewBox="82 162 348 186" class={className} aria-hidden="true">
	<mask {id}>
		<rect x="82" y="162" width="348" height="186" fill="white" />
		<path
			d="M131 185H381A26 26 0 0 0 407 211V299A26 26 0 0 0 381 325H131A26 26 0 0 0 105 299V211A26 26 0 0 0 131 185Z"
			fill="black"
		/>
		<circle cx="256" cy="255" r="45" fill="white" />
		<circle cx="143" cy="255" r="18" fill="white" />
		<circle cx="369" cy="255" r="18" fill="white" />
		<text x="256" y="280" text-anchor="middle" font-size="72" font-weight="800" fill="black">$</text
		>
	</mask>
	<rect x="82" y="162" width="348" height="186" fill="currentColor" mask="url(#{id})" />
</svg>
