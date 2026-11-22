<script lang="ts">
	import { formatDate } from '#lib/date.ts';
	import type { Comment, User } from '#lib/api/types.ts';
	import UserAvatar from '#lib/components/UserAvatar.svelte';

	function formatComment(text: string): string {
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(
				/```([^`]+)```/g,
				'<span class="text-xs font-medium text-muted-foreground">$1</span>'
			);
	}

	let { comments, currentUser }: { comments: Comment[]; currentUser?: User } = $props();
</script>

<div class="flex flex-col gap-4">
	{#each comments as comment, i}
		{@const isOwn = comment.author.email === currentUser?.email}
		<div
			class={['flex items-end gap-2', isOwn ? 'flex-row-reverse self-end' : 'self-start']}
			id={`comment-${i}`}
		>
			<UserAvatar username={comment.author.username} />
			<div class="flex w-fit max-w-[18rem] flex-col gap-0.5 bg-muted px-3 py-2">
				<div class="flex items-baseline gap-2 text-xs">
					<span class={['font-semibold', isOwn && 'text-primary-text']}>
						{comment.author.first_name}
						{comment.author.last_name}
					</span>
					<span class="text-muted-foreground">
						{formatDate(comment.date)}
					</span>
				</div>
				<div class="text-sm wrap-break-word">
					{@html formatComment(comment.content)}
				</div>
			</div>
		</div>
	{/each}
</div>
