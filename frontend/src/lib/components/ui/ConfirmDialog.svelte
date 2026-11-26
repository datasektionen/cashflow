<script lang="ts">
	import { AlertDialog } from 'bits-ui';
	import type { Snippet } from 'svelte';
	import { buttonVariants } from './Button.svelte';
	import { overlay } from './styles';

	type Props = {
		open?: boolean;
		title: string;
		description?: string;
		confirmLabel: string;
		cancelLabel: string;
		danger?: boolean;
		trigger?: Snippet<[{ props: Record<string, unknown> }]>;
		onConfirm: () => void;
		// A third choice between cancel and confirm
		alternative?: { label: string; onclick: () => void };
	};

	let {
		open = $bindable(false),
		title,
		description,
		confirmLabel,
		cancelLabel,
		danger = false,
		trigger,
		onConfirm,
		alternative
	}: Props = $props();
</script>

<AlertDialog.Root bind:open>
	{#if trigger}
		<AlertDialog.Trigger>
			{#snippet child({ props })}
				{@render trigger({ props })}
			{/snippet}
		</AlertDialog.Trigger>
	{/if}
	<AlertDialog.Portal>
		<AlertDialog.Overlay class={overlay} />
		<!-- Clicking outside cancels -->
		<AlertDialog.Content
			interactOutsideBehavior="close"
			class="fixed top-1/2 left-1/2 z-50 flex w-[calc(100%-2rem)] max-w-sm -translate-x-1/2 -translate-y-1/2 flex-col gap-4 border border-border bg-card p-6 text-foreground shadow-xl"
		>
			<div class="flex flex-col gap-1.5">
				<AlertDialog.Title class="text-lg font-semibold">{title}</AlertDialog.Title>
				{#if description}
					<AlertDialog.Description class="text-sm text-muted-foreground">
						{description}
					</AlertDialog.Description>
				{/if}
			</div>
			<div class="flex flex-col gap-2 sm:flex-row sm:justify-end">
				<AlertDialog.Cancel class={buttonVariants({ variant: 'secondary' })}>
					{cancelLabel}
				</AlertDialog.Cancel>
				{#if alternative}
					<AlertDialog.Action
						class={buttonVariants({ variant: 'danger-outline' })}
						onclick={() => {
							alternative.onclick();
							open = false;
						}}
					>
						{alternative.label}
					</AlertDialog.Action>
				{/if}
				<AlertDialog.Action
					class={buttonVariants({ variant: danger ? 'danger' : 'primary' })}
					onclick={() => {
						onConfirm();
						open = false;
					}}
				>
					{confirmLabel}
				</AlertDialog.Action>
			</div>
		</AlertDialog.Content>
	</AlertDialog.Portal>
</AlertDialog.Root>
