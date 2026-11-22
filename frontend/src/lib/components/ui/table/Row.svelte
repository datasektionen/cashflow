<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	let { class: className, children, ...rest }: HTMLAttributes<HTMLTableRowElement> = $props();
</script>

<tr
	class={cn(
		'border-b border-border transition-colors data-[state=selected]:bg-muted',
		className as string
	)}
	{...rest}
>
	{@render children?.()}
</tr>
