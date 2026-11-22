<script lang="ts">
	import { Switch as SwitchPrimitive } from 'bits-ui';
	import { cn } from 'tailwind-variants';

	let {
		checked = $bindable(false),
		ref = $bindable(null),
		class: className,
		...rest
	}: SwitchPrimitive.RootProps = $props();
</script>

<SwitchPrimitive.Root
	bind:ref
	bind:checked
	class={cn(
		'inline-flex h-5 w-9 shrink-0 cursor-pointer border-2 border-transparent bg-input transition-colors data-disabled:cursor-not-allowed data-disabled:opacity-50 data-[state=checked]:bg-primary',
		className as string
	)}
	{...rest}
>
	<SwitchPrimitive.Thumb
		class="pointer-events-none block aspect-square h-full bg-white transition-transform duration-200 ease-out data-[state=checked]:translate-x-4"
	/>
</SwitchPrimitive.Root>
