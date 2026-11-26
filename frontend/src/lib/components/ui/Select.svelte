<script lang="ts" generics="T extends string">
	import { Select as SelectPrimitive } from 'bits-ui';
	import { Check, ChevronDown } from '@lucide/svelte';
	import { cn } from 'tailwind-variants';
	import { surface, menuItem } from './styles';

	type Props = {
		value?: T;
		items: { value: T; label: string }[];
		id?: string;
		class?: string;
		onValueChange?: (value: T) => void;
	};

	let { value = $bindable(), items, id, class: className, onValueChange }: Props = $props();

	const selected = $derived(items.find((i) => i.value === value));
</script>

<SelectPrimitive.Root
	type="single"
	{items}
	bind:value={() => value ?? '', (v) => (value = v as T)}
	onValueChange={(v) => onValueChange?.(v as T)}
>
	<SelectPrimitive.Trigger
		{id}
		class={cn(
			'flex h-9 w-full cursor-pointer items-center justify-between gap-2 border border-input bg-card px-3 text-sm outline-none ring-inset focus-visible:border-primary focus-visible:ring-1 focus-visible:ring-primary data-disabled:cursor-not-allowed data-disabled:opacity-60 data-placeholder:text-muted-foreground',
			className
		)}
	>
		<span class="truncate">{selected?.label}</span>
		<ChevronDown class="size-4 shrink-0 text-muted-foreground" />
	</SelectPrimitive.Trigger>
	<SelectPrimitive.Portal>
		<SelectPrimitive.Content
			sideOffset={4}
			class={cn(surface, 'max-h-72 w-(--bits-select-anchor-width) min-w-32')}
		>
			<SelectPrimitive.Viewport>
				{#each items as item (item.value)}
					<SelectPrimitive.Item value={item.value} label={item.label} class={cn(menuItem, 'pr-8')}>
						{#snippet children({ selected })}
							{item.label}
							{#if selected}<Check class="absolute right-2" />{/if}
						{/snippet}
					</SelectPrimitive.Item>
				{/each}
			</SelectPrimitive.Viewport>
		</SelectPrimitive.Content>
	</SelectPrimitive.Portal>
</SelectPrimitive.Root>
