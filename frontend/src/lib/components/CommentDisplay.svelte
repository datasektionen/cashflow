<script lang="ts">
	import { locale } from 'svelte-i18n';
	import type { Comment, User } from '$lib/api/types';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import { api } from '$lib/api';

	function formatComment(text: string): string {
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(
				/```([^`]+)```/g,
				'<span class="uppercase text-xs tracking-wide opacity-60 font-medium">$1</span>'
			);
	}

	export type CommentDisplayProps = {
		comments: Comment[];
		currentUser?: User;
		// 'chat' = green own/other bubbles (default); 'compact' = calm, left-aligned, muted list.
		variant?: 'chat' | 'compact';
	};

	let { comments, currentUser, variant = 'chat' }: CommentDisplayProps = $props();

	const avatarMap = $derived(
		api.profilePictures.getMany([...new Set(comments.map((c) => c.author.username))])
	);
</script>

{#if variant === 'compact'}
	<div class="flex flex-col gap-3">
		{#each comments as comment}
			<div class="flex items-start gap-2">
				{#await avatarMap}
					<UserAvatar placeholder class="size-6 shrink-0" />
				{:then urls}
					<UserAvatar url={urls[comment.author.username] ?? undefined} class="size-6 shrink-0" />
				{/await}
				<div class="flex flex-col">
					<div class="flex items-baseline gap-2">
						<span class="text-xs font-medium text-base-text dark:text-dark-base-text">
							{comment.author.first_name}
							{comment.author.last_name}
						</span>
						<span class="text-xs text-base-subtle opacity-70 dark:text-dark-base-subtle">
							{new Date(comment.date).toLocaleDateString($locale ?? 'sv-SE')}
						</span>
					</div>
					<div class="text-sm text-base-subtle dark:text-dark-base-subtle">
						{@html formatComment(comment.content)}
					</div>
				</div>
			</div>
		{/each}
	</div>
{:else}
	<div class="flex flex-col gap-4">
		{#each comments as comment}
			{@const isOwn = comment.author.email === currentUser?.email}
			<div
				class={[
					'flex items-end gap-2',
					isOwn ? 'flex-row-reverse self-end' : 'flex-row self-start'
				]}
			>
				{#await avatarMap}
					<UserAvatar placeholder class="shrink-0 ring-2 ring-white dark:ring-dark-base-100" />
				{:then urls}
					<UserAvatar
						url={urls[comment.author.username] ?? undefined}
						class="shrink-0 ring-2 ring-white dark:ring-dark-base-100"
					/>
				{/await}
				<div
					class={[
						'min-h-12 w-fit max-w-[16rem] p-2',
						isOwn ? 'bg-money-green-500' : 'bg-base-300 dark:bg-dark-base-300'
					]}
				>
					<div class="flex items-baseline gap-2">
						<span
							class={[
								'text-xs font-medium uppercase',
								isOwn ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
							]}
						>
							{comment.author.first_name}
							{comment.author.last_name}
						</span>
						<span
							class={[
								'text-xs opacity-60',
								isOwn ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
							]}
						>
							{new Date(comment.date).toLocaleDateString($locale ?? 'sv-SE')}
						</span>
					</div>
					<div class={['text-sm', isOwn && 'text-white']}>
						{@html formatComment(comment.content)}
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}
