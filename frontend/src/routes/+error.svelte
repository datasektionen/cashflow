<script lang="ts">
	import { Bug } from '@lucide/svelte';
	import { page } from '$app/state';
</script>

<div class="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
	<div class="flex size-14 items-center justify-center bg-muted">
		<Bug class="size-7 text-muted-foreground" />
	</div>
	<h1 class="text-sm text-muted-foreground">{page.error?.message}</h1>
</div>
