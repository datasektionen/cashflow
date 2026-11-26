<script lang="ts">
	import type { HTMLThAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	type Props = HTMLThAttributes & { align?: 'left' | 'right' | 'center' };

	let { align = 'left', class: className, children, ...rest }: Props = $props();
</script>

<th
	class={cn(
		'h-10 px-3 text-[11px] font-semibold tracking-wide whitespace-nowrap text-muted-foreground uppercase',
		align === 'right' ? 'text-right' : align === 'center' ? 'text-center' : 'text-left',
		className as string
	)}
	{...rest}
>
	{@render children?.()}
</th>
