<script lang="ts">
	import { locale } from 'svelte-i18n';
	import type { Comment, User } from '$lib/api/types';
	import { ScrollArea } from 'bits-ui';
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
	};

	let { comments, currentUser }: CommentDisplayProps = $props();

	const avatarMap = $derived(
		api.profilePictures.getMany([...new Set(comments.map((c) => c.author.username))])
	);
</script>

<div class="flex flex-col gap-4 lg:hidden">
	{#each comments as comment}
		{@const isOwn = comment.author.email === currentUser?.email}
		<div
			class={['flex items-end gap-2', isOwn ? 'flex-row-reverse self-end' : 'flex-row self-start']}
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

<ScrollArea.Root class="relative hidden w-full overflow-hidden lg:block">
	<ScrollArea.Viewport class="h-full max-h-50 w-full">
		<div class="flex flex-col gap-4 p-4">
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
	</ScrollArea.Viewport>

	<ScrollArea.Scrollbar
		orientation="vertical"
		class="hover:bg-dark-10 data-[state=visible]:animate-in data-[state=hidden]:animate-out data-[state=hidden]:fade-out-0 data-[state=visible]:fade-in-0 flex w-2.5 touch-none rounded-none border-l border-l-transparent bg-base-subtle p-px transition-all duration-200 select-none hover:w-3 dark:bg-dark-base-subtle"
	>
		<ScrollArea.Thumb class="flex-1 rounded-none bg-base-400 dark:bg-dark-base-400" />
	</ScrollArea.Scrollbar>
	<ScrollArea.Scrollbar
		orientation="horizontal"
		class="flex h-2.5 touch-none rounded-none border-t border-t-transparent bg-base-300 p-px transition-all duration-200 select-none hover:h-3 dark:bg-dark-base-300"
	>
		<ScrollArea.Thumb class="rounded-none bg-base-400 dark:bg-dark-base-400" />
	</ScrollArea.Scrollbar>
	<ScrollArea.Corner />
</ScrollArea.Root>
