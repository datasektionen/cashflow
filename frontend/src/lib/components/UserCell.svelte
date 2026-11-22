<script lang="ts">
	import type { Profile } from '#lib/api/types.ts';
	import { avatarUrl } from '#lib/avatars.ts';
	import { Avatar } from '#lib/components/ui/index.ts';
	import UserLink from '#lib/components/UserLink.svelte';

	let { user }: { user: Profile } = $props();

	const initials = $derived(`${user.first_name.charAt(0)}${user.last_name.charAt(0)}`);
	const url = $derived(avatarUrl(user.username));
</script>

<span class="flex min-w-0 items-center gap-2">
	{#await url}
		<Avatar fallback={initials} class="size-6" />
	{:then src}
		<Avatar {src} fallback={initials} class="size-6" />
	{/await}
	<UserLink {user} class="relative z-10 truncate" />
</span>
