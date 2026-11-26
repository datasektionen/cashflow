<script lang="ts">
	import type { HTMLTdAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	type Props = HTMLTdAttributes & { align?: 'left' | 'right' | 'center' };

	let { align = 'left', class: className, children, ...rest }: Props = $props();
</script>

<td
	class={cn(
		'h-12 px-3 align-middle',
		align === 'right' && 'text-right whitespace-nowrap',
		align === 'center' && 'text-center',
		className as string
	)}
	{...rest}
>
	{@render children?.()}
</td>
