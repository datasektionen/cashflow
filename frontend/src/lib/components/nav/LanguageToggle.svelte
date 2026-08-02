<script lang="ts">
	import { locale } from 'svelte-i18n';
	import FlagEN from '$lib/components/FlagEN.svelte';
	import FlagSE from '$lib/components/FlagSE.svelte';

	const isSwedish = $derived($locale?.toLowerCase().startsWith('sv') ?? true);

	function toggle() {
		const next = isSwedish ? 'en' : 'sv';
		locale.set(next);
		localStorage.setItem('locale', next);
	}
</script>

<div class="relative flex h-5 w-16 flex-row">
	<button
		class="relative flex h-full w-full cursor-pointer bg-white/10 transition-colors hover:bg-white/20"
		onclick={toggle}
	>
		<FlagSE
			class={[
				'absolute top-0 h-5 w-8 transition-all',
				isSwedish ? 'left-8 opacity-100' : 'left-0 opacity-0'
			]}
		/>
		<span
			class={[
				'absolute top-0 left-0 h-5 w-8 transition-all',
				'flex items-center justify-center text-xs font-medium text-white uppercase'
			]}
		>
			SV
		</span>

		<FlagEN
			class={[
				'absolute top-0 h-5 w-8 transition-all',
				isSwedish ? 'left-8 opacity-0' : 'left-0 opacity-100'
			]}
		/>

		<span
			class={[
				'absolute top-0 left-8 h-5 w-8 transition-all',
				'flex items-center justify-center text-xs font-medium text-white uppercase',
				isSwedish && 'opacity-0'
			]}
		>
			EN
		</span>
	</button>
</div>
