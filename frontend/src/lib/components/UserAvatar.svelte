<script lang="ts">
	import { api } from '$lib/api';

	type UserAvatarProps = {
		username: string;
		class?: string;
	};

	let { username, class: className, ...more }: UserAvatarProps = $props();
</script>

{#await api.profilePictures.get(username)}
	<p>Loading</p>
{:then url}
	<img class={['size-8 rounded-full object-cover', className]} src={url} alt="avatar" {...more} />
{:catch error}
	<p>Failed</p>
{/await}
