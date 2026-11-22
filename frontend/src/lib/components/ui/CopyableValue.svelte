<script lang="ts">
	import { Check, Copy } from '@lucide/svelte';
	import { cn } from 'tailwind-variants';
	import type { Component } from 'svelte';
	import type { ClassValue } from 'svelte/elements';
	import { clipboard } from '#lib/clipboard.svelte.ts';

	let {
		display,
		value,
		label,
		icon: Icon,
		class: className
	}: {
		display: string | number;
		value?: string | number;
		/** Names the value on hover and for screen readers when the icon is all that labels it */
		label?: string;
		icon?: Component;
		class?: ClassValue;
	} = $props();

	const clip = clipboard();
</script>

<button
	type="button"
	onclick={() => clip.copy(String(value ?? display))}
	title={label ? `${label}: ${display}` : String(display)}
	class={cn(
		'group flex h-7 max-w-60 cursor-pointer items-center gap-1.5 border border-border bg-card px-2 text-xs text-muted-foreground transition-colors hover:border-foreground/50 hover:text-foreground',
		className as string
	)}
>
	{#if Icon}<Icon class="size-3.5 shrink-0" aria-hidden="true" />{/if}
	<span class="truncate">
		{#if label}<span class="sr-only">{label}:</span>{/if}
		{display}
	</span>
	{#if clip.copied}
		<Check class="size-3 shrink-0" />
	{:else}
		<Copy class="size-3 shrink-0 transition-transform group-hover:scale-110" />
	{/if}
</button>
