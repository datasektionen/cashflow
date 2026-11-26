<script lang="ts">
	import type { HTMLTableAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	let { class: className, children, ...rest }: HTMLTableAttributes = $props();
</script>

<div class="relative w-full overflow-x-auto">
	<table class={cn('w-full caption-bottom text-sm tabular-nums', className as string)} {...rest}>
		{@render children?.()}
	</table>
</div>
