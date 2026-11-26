<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	let { class: className, children, ...rest }: HTMLAttributes<HTMLTableSectionElement> = $props();
</script>

<tfoot
	class={cn('border-t border-border font-medium [&>tr]:last:border-b-0', className as string)}
	{...rest}
>
	{@render children?.()}
</tfoot>
