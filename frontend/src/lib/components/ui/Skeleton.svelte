<script lang="ts">
	import { cn } from 'tailwind-variants';

	let { class: className = '' }: { class?: string } = $props();
</script>

<div class={cn('animate-pulse bg-muted', className)}></div>
