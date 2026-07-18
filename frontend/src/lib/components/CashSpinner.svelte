<script lang="ts">
	import { CircleDollarSign } from '@lucide/svelte';

	let { class: className = '' }: { class?: string } = $props();
</script>

<CircleDollarSign class="m-auto animate-spin {className}" />
