<script lang="ts">
	import type { Profile } from '$lib/api/types';

	let { user }: { user: Profile } = $props();
</script>

<!-- stopPropagation lets the link live inside clickable table rows without triggering the row's navigation -->
<a
	href="/{user.username}/claims"
	onclick={(event) => event.stopPropagation()}
	class="hover:underline"
>
	{user.first_name}
	{user.last_name}
</a>
