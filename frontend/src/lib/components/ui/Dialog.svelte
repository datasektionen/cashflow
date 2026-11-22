<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Dialog as DialogPrimitive } from 'bits-ui';
	import { X } from '@lucide/svelte';
	import type { Snippet } from 'svelte';
	import { overlay } from './styles';

	type Props = {
		open?: boolean;
		title: string;
		description?: string;
		trigger?: Snippet<[{ props: Record<string, unknown> }]>;
		footer?: Snippet;
		children?: Snippet;
	};

	let { open = $bindable(false), title, description, trigger, footer, children }: Props = $props();
</script>

<DialogPrimitive.Root bind:open>
	{#if trigger}
		<DialogPrimitive.Trigger>
			{#snippet child({ props })}
				{@render trigger({ props })}
			{/snippet}
		</DialogPrimitive.Trigger>
	{/if}
	<DialogPrimitive.Portal>
		<DialogPrimitive.Overlay class={overlay} />
		<DialogPrimitive.Content
			class="fixed top-1/2 left-1/2 z-50 flex max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 flex-col gap-4 overflow-y-auto border border-border bg-card p-6 text-foreground shadow-xl"
		>
			<div class="flex flex-col gap-1.5 pr-6">
				<DialogPrimitive.Title class="text-lg font-semibold">{title}</DialogPrimitive.Title>
				{#if description}
					<DialogPrimitive.Description class="text-sm text-muted-foreground">
						{description}
					</DialogPrimitive.Description>
				{/if}
			</div>
			{@render children?.()}
			{#if footer}
				<div class="flex flex-col gap-2 sm:flex-row sm:justify-end">{@render footer()}</div>
			{/if}
			<DialogPrimitive.Close
				class="absolute top-4 right-4 cursor-pointer p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
				aria-label={$_('close')}
			>
				<X class="size-4" />
			</DialogPrimitive.Close>
		</DialogPrimitive.Content>
	</DialogPrimitive.Portal>
</DialogPrimitive.Root>
