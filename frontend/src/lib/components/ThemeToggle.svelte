<script lang="ts">
	import { Moon, Sun } from '@lucide/svelte';

	// Same key as the previously used flowbite-svelte DarkMode component, so
	// existing preferences carry over. The initial class is applied by the
	// inline script in app.html before first paint.
	const STORAGE_KEY = 'color-theme';

	let dark = $state(
		typeof document !== 'undefined' && document.documentElement.classList.contains('dark')
	);

	function toggle() {
		dark = !dark;
		document.documentElement.classList.toggle('dark', dark);
		localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light');
	}
</script>

<button
	type="button"
	onclick={toggle}
	aria-label="Toggle dark mode"
	class="cursor-pointer rounded-full p-2 transition-colors hover:bg-white/10 dark:hover:bg-dark-base-300"
>
	{#if dark}
		<Sun class="size-5" />
	{:else}
		<Moon class="size-5" />
	{/if}
</button>
