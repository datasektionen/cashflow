<script lang="ts">
	import type { HTMLTextareaAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	type Props = HTMLTextareaAttributes & { ref?: HTMLTextAreaElement | null };

	let { value = $bindable(), ref = $bindable(null), class: className, ...rest }: Props = $props();
</script>

<textarea
	bind:this={ref}
	bind:value
	class={cn(
		'flex min-h-20 w-full border border-input bg-card px-3 py-2 text-sm transition-colors outline-none ring-inset placeholder:text-muted-foreground focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-60 aria-invalid:border-danger',
		className as string
	)}
	{...rest}
></textarea>
