<script lang="ts" generics="T extends string">
	import { ToggleGroup } from 'bits-ui';
	import { cn } from 'tailwind-variants';

	type Props = {
		value: T;
		items: { value: T; label: string }[];
		size?: 'sm' | 'md';
		class?: string;
		onValueChange?: (value: T) => void;
	};

	let {
		value = $bindable(),
		items,
		size = 'md',
		class: className,
		onValueChange
	}: Props = $props();
</script>

<ToggleGroup.Root
	type="single"
	bind:value={
		() => value,
		(v) => {
			if (!v) return;
			value = v as T;
			onValueChange?.(value);
		}
	}
	class={cn('inline-flex items-center border border-input bg-card', className)}
>
	{#each items as item (item.value)}
		<ToggleGroup.Item
			value={item.value}
			class={cn(
				'cursor-pointer font-semibold tracking-wide whitespace-nowrap text-muted-foreground uppercase transition-colors hover:bg-muted hover:text-foreground data-[state=on]:bg-primary data-[state=on]:text-primary-foreground',
				size === 'sm' ? 'h-7 px-2.5 text-[11px]' : 'h-8 px-3.5 text-xs'
			)}
		>
			{item.label}
		</ToggleGroup.Item>
	{/each}
</ToggleGroup.Root>
