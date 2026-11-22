<script lang="ts">
	import { locale } from 'svelte-i18n';
	import { cn } from 'tailwind-variants';
	import { LOCALE_STORAGE_KEY } from '#lib/i18n/index.ts';
	import FlagEN from '#lib/components/FlagEN.svelte';
	import FlagSE from '#lib/components/FlagSE.svelte';

	let { class: className }: { class?: string } = $props();

	const isSwedish = $derived($locale?.toLowerCase().startsWith('sv') ?? true);

	function toggle() {
		const next = isSwedish ? 'en' : 'sv';
		locale.set(next);
		localStorage.setItem(LOCALE_STORAGE_KEY, next);
	}
</script>

<button
	type="button"
	aria-label={isSwedish ? 'Switch to English' : 'Byt till svenska'}
	onclick={toggle}
	class={cn(
		'group relative grid h-7 w-18 cursor-pointer grid-cols-2 items-center border border-white/35 p-0.5 text-[11px] font-bold tracking-wider text-white/75 transition-colors select-none hover:border-white/70 hover:text-white active:scale-95',
		className
	)}
>
	<span
		aria-hidden="true"
		class={[
			'absolute inset-y-0.5 left-0.5 w-[calc(50%-0.125rem)] overflow-hidden shadow-sm transition-transform duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] motion-reduce:transition-none',
			!isSwedish && 'translate-x-full'
		]}
	>
		{#if isSwedish}
			<FlagSE class="block size-full" />
		{:else}
			<FlagEN class="block size-full" />
		{/if}
	</span>
	<span aria-hidden="true" class="text-center">SV</span>
	<span aria-hidden="true" class="text-center">EN</span>
</button>
