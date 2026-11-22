<script lang="ts">
	import { tick } from 'svelte';
	import { _ } from 'svelte-i18n';
	import { MessageSquarePlus } from '@lucide/svelte';
	import type { Comment, User } from '#lib/api/types.ts';
	import CommentList from '#lib/components/claim/CommentList.svelte';
	import { Button, Card, Spinner, Textarea } from '#lib/components/ui/index.ts';
	import { failed, success } from '#lib/stores/alerts.ts';

	type Props = {
		comments: Comment[];
		currentUser?: User;
		onSubmit: (content: string) => Promise<Comment>;
	};

	let { comments = $bindable(), currentUser, onSubmit }: Props = $props();

	let open = $state(false);
	let form: HTMLDivElement | undefined = $state();

	async function openForm() {
		open = true;
		await tick();
		form?.querySelector('textarea')?.focus({ preventScroll: true });
		form?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
	}
	let content = $state('');
	let pending = $state(false);

	async function submit() {
		pending = true;
		try {
			comments = [...comments, await onSubmit(content)];
			open = false;
			content = '';
			success($_('comment_submitted'));
			await tick();
			document
				.getElementById(`comment-${comments.length - 1}`)
				?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
		} catch (e) {
			failed(e, $_('comment_submission_failed'));
		} finally {
			pending = false;
		}
	}
</script>

<Card title={$_('expense_comments')} padded={false}>
	{#snippet actions()}
		{#if !open}
			<Button variant="secondary" size="sm" onclick={openForm}>
				<MessageSquarePlus />
				{$_('add_comment')}
			</Button>
		{/if}
	{/snippet}
	{#if open || comments.length > 0}
		<div class="flex flex-col gap-4 p-5">
			{#if open}
				<div bind:this={form} class="flex scroll-m-4 flex-col gap-2">
					<Textarea
						bind:value={content}
						rows={3}
						aria-label={$_('add_comment')}
						placeholder={$_('add_comment_placeholder')}
					/>
					<div class="flex justify-end gap-2">
						<Button variant="ghost" size="sm" onclick={() => (open = false)}>
							{$_('cancel')}
						</Button>
						<Button size="sm" onclick={submit} disabled={pending || !content.trim()}>
							{#if pending}<Spinner />{/if}
							{$_('submit')}
						</Button>
					</div>
				</div>
			{/if}
			<CommentList {comments} {currentUser} />
		</div>
	{/if}
</Card>
