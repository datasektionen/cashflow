<script lang="ts">
	import { Separator as SeparatorPrimitive } from 'bits-ui';
	import { cn } from 'tailwind-variants';

	let { class: className, ...rest }: SeparatorPrimitive.RootProps = $props();
</script>

<SeparatorPrimitive.Root
	class={cn('h-px w-full shrink-0 bg-border', className as string)}
	{...rest}
/>
