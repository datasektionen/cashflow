<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Moon, Sun } from '@lucide/svelte';
	import { Button } from '#lib/components/ui/index.ts';
	import { cn } from 'tailwind-variants';

	let { class: className }: { class?: string } = $props();

	// Also read by the inline script in app.html
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

<Button
	variant="ghost"
	size="icon"
	onclick={toggle}
	aria-label={$_('toggle_theme')}
	class={cn('text-muted-foreground hover:text-foreground', className)}
>
	{#if dark}
		<Sun />
	{:else}
		<Moon />
	{/if}
</Button>
