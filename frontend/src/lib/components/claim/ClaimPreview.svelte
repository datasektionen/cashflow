<script lang="ts" generics="T extends Expense | Invoice">
	import type { Snippet } from 'svelte';
	import { _ } from 'svelte-i18n';
	import { ExternalLink, FileX } from '@lucide/svelte';
	import type { Expense, Invoice, User } from '#lib/api/types.ts';
	import { Button, Card, EmptyState, Skeleton } from '#lib/components/ui/index.ts';
	import ReceiptViewer from '#lib/components/ReceiptViewer.svelte';
	import PartsTable from '#lib/components/PartsTable.svelte';
	import CommentList from '#lib/components/claim/CommentList.svelte';
	import ClaimChips from './ClaimChips.svelte';

	type Props = {
		claim: Promise<T>;
		href: string;
		currentUser?: User;
		// In a footer below the receipt and parts, next to Open
		actions?: Snippet<[T]>;
	};

	let { claim, href, currentUser, actions }: Props = $props();
</script>

<Card padded={false} class="flex h-full w-full flex-col">
	{#await claim}
		<div class="flex flex-col gap-3 border-b border-border px-5 py-4">
			<Skeleton class="h-6 w-3/5" />
			<div class="flex flex-wrap gap-2">
				{#each ['w-16', 'w-32', 'w-28', 'w-24'] as width, i (i)}
					<Skeleton class="h-7 {width}" />
				{/each}
			</div>
		</div>
		<Skeleton class="min-h-0 flex-1" />
		<div class="flex shrink-0 flex-col divide-y divide-border border-t border-border">
			{#each { length: 3 }, i (i)}
				<div class="flex h-12 items-center justify-between gap-4 px-3">
					<Skeleton class="h-4 w-2/5" />
					<Skeleton class="h-4 w-20" />
				</div>
			{/each}
		</div>
		<div class="shrink-0 border-t border-border p-3"><Skeleton class="h-9" /></div>
	{:then c}
		{@const hasFiles = c.files.length > 0}
		<div class="flex flex-col gap-3 border-b border-border px-5 py-4">
			<h2 class="text-lg leading-tight font-bold wrap-break-word">
				{c.description}
			</h2>
			<ClaimChips claim={c} linkOwner />
		</div>

		<div class={['flex flex-col bg-muted/40', hasFiles && 'min-h-0 flex-1']}>
			{#if hasFiles}
				<ReceiptViewer source={c.files.map((f) => f.file)} />
			{:else}
				<EmptyState icon={FileX} title={$_('expense_no_files')} class="border-0 py-8" />
			{/if}
		</div>

		<div
			class={[
				'flex flex-col overflow-y-auto border-t border-border',
				hasFiles ? 'max-h-[40%] shrink-0' : 'min-h-0 flex-1'
			]}
		>
			<PartsTable parts={c.parts} owner={c.owner} {currentUser} />
			{#if c.comments.length > 0}
				<div class="border-t border-border px-5 py-4">
					<CommentList comments={c.comments} {currentUser} />
				</div>
			{/if}
		</div>

		<div class="grid shrink-0 auto-cols-fr grid-flow-col gap-2 border-t border-border p-3">
			<Button variant="secondary" {href}>
				{$_('admin_confirmable.preview.open_detail')}
				<ExternalLink />
			</Button>
			{@render actions?.(c)}
		</div>
	{:catch}
		<p class="flex flex-1 items-center justify-center text-sm text-danger">
			{$_('action_failed')}
		</p>
	{/await}
</Card>
