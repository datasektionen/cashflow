<script lang="ts">
	import { Flag } from '@lucide/svelte';

	type Tone = 'attested' | 'confirmed' | 'paid' | 'voucher' | 'neutral' | 'flagged';

	let { tone, label, mono = false }: { tone: Tone; label: string; mono?: boolean } = $props();

	const dotClass: Record<Exclude<Tone, 'flagged'>, string> = {
		attested: 'bg-money-green-400 dark:bg-money-green-500',
		confirmed: 'bg-money-green-500 dark:bg-money-green-400',
		paid: 'bg-money-green-600 dark:bg-money-green-400',
		voucher: 'bg-money-green-700 dark:bg-money-green-300',
		neutral: 'bg-base-400 dark:bg-dark-base-400'
	};
</script>

{#if tone === 'flagged'}
	<span class="flex items-center gap-1 text-xs text-amber-800 dark:text-amber-400">
		<Flag class="size-3 shrink-0" />
		{label}
	</span>
{:else}
	<span
		class={[
			'flex items-center gap-1.5 text-xs',
			mono && 'font-mono',
			tone === 'neutral' && 'text-base-subtle dark:text-dark-base-subtle'
		]}
	>
		<span class={['inline-block size-1.5 shrink-0 rounded-full', dotClass[tone]]}></span>
		{label}
	</span>
{/if}
