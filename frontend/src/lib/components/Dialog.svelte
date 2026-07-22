<script lang="ts">
	import { Dialog, type WithoutChildren } from 'bits-ui';
	import { X } from '@lucide/svelte';
	import type { Snippet } from 'svelte';

	type Props = Dialog.RootProps & {
		title: Snippet;
		description?: Snippet;
		triggerContent: Snippet;
		contentProps?: WithoutChildren<Dialog.ContentProps>;
	};

	let {
		open = $bindable(false),
		children,
		triggerContent,
		title,
		description,
		contentProps,
		...restProps
	}: Props = $props();
</script>

<Dialog.Root bind:open {...restProps}>
	<Dialog.Trigger>
		{@render triggerContent()}
	</Dialog.Trigger>
	<Dialog.Portal class={['m-auto']}>
		<Dialog.Overlay class={['fixed top-0 left-0 z-40 size-full bg-black opacity-50 blur-2xl']} />
		<Dialog.Content
			class={[
				'fixed top-1/2 left-1/2 z-50 w-100 -translate-x-1/2 -translate-y-1/2 bg-base-300 shadow-2xl dark:bg-dark-base-300',
				'p-8'
			]}
			{...contentProps}
		>
			<Dialog.Close
				class="text-subtle absolute top-0 right-0 m-4 cursor-pointer transition-all hover:scale-110 dark:text-dark-base-subtle"
			>
				<X />
			</Dialog.Close>

			<Dialog.Title>
				{@render title()}
			</Dialog.Title>

			<Dialog.Description>
				{@render description?.()}
			</Dialog.Description>
			{@render children?.()}
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
