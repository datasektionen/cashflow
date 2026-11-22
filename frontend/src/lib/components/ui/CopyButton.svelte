<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Check, Copy } from '@lucide/svelte';
	import { cn } from 'tailwind-variants';
	import { clipboard } from '#lib/clipboard.svelte.ts';

	let { value, class: className }: { value: string; class?: string } = $props();

	const clip = clipboard();
</script>

<button
	type="button"
	aria-label={$_('copy')}
	onclick={() => clip.copy(value)}
	class={cn(
		'inline-flex size-8 shrink-0 cursor-pointer items-center justify-center align-middle text-muted-foreground transition hover:bg-muted hover:text-foreground [&_svg]:size-4',
		className
	)}
>
	{#if clip.copied}<Check />{:else}<Copy />{/if}
</button>
