<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	let { class: className, children, ...rest }: HTMLAttributes<HTMLTableSectionElement> = $props();
</script>

<thead class={cn('[&_tr]:border-b [&_tr]:border-border', className as string)} {...rest}>
	{@render children?.()}
</thead>
