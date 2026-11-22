<script lang="ts">
	import { Avatar as AvatarPrimitive } from 'bits-ui';
	import { cn } from 'tailwind-variants';

	type Props = {
		src?: string | null;
		fallback?: string;
		class?: string;
	};

	let { src, fallback = '', class: className }: Props = $props();
</script>

<AvatarPrimitive.Root
	class={cn('relative flex size-8 shrink-0 overflow-hidden bg-muted', className)}
>
	{#if src}
		<AvatarPrimitive.Image {src} alt="" class="aspect-square size-full object-cover object-top" />
	{/if}
	<AvatarPrimitive.Fallback
		class="flex size-full items-center justify-center text-xs font-medium text-muted-foreground"
	>
		{fallback}
	</AvatarPrimitive.Fallback>
</AvatarPrimitive.Root>
