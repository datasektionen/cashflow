<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';
	import { cn } from 'tailwind-variants';

	type Props = Omit<HTMLInputAttributes, 'value'> & {
		value?: HTMLInputAttributes['value'];
		ref?: HTMLInputElement | null;
	};

	let { value = $bindable(), ref = $bindable(null), class: className, ...rest }: Props = $props();
</script>

<input
	bind:this={ref}
	bind:value
	class={cn(
		'flex h-9 w-full min-w-0 border border-input bg-card px-3 text-sm transition-colors outline-none ring-inset placeholder:text-muted-foreground focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-60 aria-invalid:border-danger aria-invalid:ring-danger/20',
		className as string
	)}
	{...rest}
/>
