<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { cn } from 'tailwind-variants';
	import { surface } from '../styles';

	let {
		sideOffset = 4,
		align = 'end',
		class: className,
		...rest
	}: DropdownMenu.ContentProps = $props();
</script>

<DropdownMenu.Portal>
	<DropdownMenu.Content
		{sideOffset}
		{align}
		class={cn(surface, 'min-w-44', className as string)}
		{...rest}
	/>
</DropdownMenu.Portal>
