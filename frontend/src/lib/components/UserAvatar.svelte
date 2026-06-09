<script lang="ts">
	import { api } from '$lib/api';

	type UserAvatarProps = {
		url?: string;
		username?: string;
		placeholder?: boolean;
		class?: string;
	};

	let { url, username, placeholder = false, class: className, ...more }: UserAvatarProps = $props();

	const resolved =
		placeholder || (!url && !username)
			? Promise.reject()
			: url
				? Promise.resolve(url)
				: api.profilePictures.get(username!);
</script>

{#await resolved}
	<div class={['size-8 rounded-full object-cover']}></div>
{:then src}
	<img class={['size-8 rounded-full object-cover', className]} {src} alt="avatar" {...more} />
{:catch e}
	<div class={['size-8 rounded-full object-cover']}></div>
{/await}
