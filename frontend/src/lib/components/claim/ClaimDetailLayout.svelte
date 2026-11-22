<script lang="ts">
	import type { Snippet } from 'svelte';
	import { _ } from 'svelte-i18n';
	import { CopyButton } from '#lib/components/ui/index.ts';
	import type { Expense, Invoice } from '#lib/api/types.ts';
	import ReceiptLayout from '#lib/components/ReceiptLayout.svelte';
	import ClaimChips from './ClaimChips.svelte';

	type Props = {
		claim: Expense | Invoice;
		// Next to the title on desktop, in a bar fixed to the bottom on phones
		actions?: Snippet;
		children: Snippet;
	};

	let { claim, actions, children }: Props = $props();
</script>

<ReceiptLayout files={claim.files.map((f) => f.file)}>
	{#snippet header()}
		<!-- Buttons drop below the title when it doesn't fit beside them -->
		<header class="flex items-start gap-x-4 gap-y-3 lg:flex-wrap">
			<div class="group flex min-w-0 grow items-start gap-1 pt-0.5">
				<h1 class="min-w-0 text-2xl font-bold tracking-tight wrap-break-word">
					{claim.description}
				</h1>
				<CopyButton
					value={claim.description}
					class="opacity-0 group-hover:opacity-100 focus-visible:opacity-100 pointer-coarse:hidden"
				/>
			</div>
			{#if actions}
				<div
					class="flex justify-end gap-2 max-lg:fixed max-lg:inset-x-0 max-lg:bottom-0 max-lg:z-30 max-lg:border-t max-lg:border-border max-lg:bg-card max-lg:px-4 max-lg:pt-3 max-lg:pb-[max(0.75rem,env(safe-area-inset-bottom))]"
				>
					{@render actions()}
				</div>
			{/if}
		</header>
		<ClaimChips {claim} />
	{/snippet}
	{@render children()}
	{#if actions}
		<!-- Room for the bottom bar on phones -->
		<div class="h-16 lg:hidden"></div>
	{/if}
</ReceiptLayout>
