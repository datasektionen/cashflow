<script lang="ts">
	import { Check, Copy } from '@lucide/svelte';
	import type { ClassValue } from 'svelte/elements';

	let {
		display,
		value = display,
		class: className
	}: {
		display: string | number;
		value?: string | number;
		class?: ClassValue;
	} = $props();

	let copied = $state(false);

	function copy() {
		navigator.clipboard.writeText(String(value));
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<button
	type="button"
	onclick={copy}
	class={[
		'group flex max-w-full cursor-pointer items-center gap-1.5 border border-base-500 px-2.5 py-1 text-xs text-base-subtle transition-colors hover:text-base-text dark:border-dark-base-200 dark:text-dark-base-subtle dark:hover:text-dark-base-text',
		className
	]}
>
	<span class="truncate">{display}</span>
	{#if copied}
		<Check class="size-3.5 shrink-0" />
	{:else}
		<Copy class="size-3.5 shrink-0 transition-transform group-hover:scale-110" />
	{/if}
</button>
