<script lang="ts">
	import { Bug } from '@lucide/svelte';
	import { page } from '$app/state';
</script>

<div class="flex min-h-[70vh] flex-col items-center justify-center gap-4 text-center">
	<Bug class="size-16 text-base-subtle dark:text-dark-base-subtle" />
	<h1 class="text-base-subtle dark:text-dark-base-subtle">{page.error?.message}</h1>
</div>
