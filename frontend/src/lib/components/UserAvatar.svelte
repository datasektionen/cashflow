<script lang="ts">
	import { avatarUrl } from '#lib/avatars.ts';
	import { Avatar } from '#lib/components/ui/index.ts';

	type UserAvatarProps = {
		url?: string;
		username?: string;
		placeholder?: boolean;
		class?: string;
	};

	let { url, username, placeholder = false, class: className }: UserAvatarProps = $props();

	const resolved = $derived(
		placeholder || (!url && !username)
			? Promise.resolve(null)
			: url
				? Promise.resolve(url)
				: avatarUrl(username!)
	);
</script>

{#await resolved}
	<Avatar class={className} />
{:then src}
	<Avatar {src} class={className} />
{/await}
