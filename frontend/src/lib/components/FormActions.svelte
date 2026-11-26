<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { BanknoteArrowUp } from '@lucide/svelte';
	import { Button, Spinner } from '#lib/components/ui/index.ts';

	let {
		cancelHref,
		submitLabel,
		submitting
	}: { cancelHref: string; submitLabel: string; submitting: boolean } = $props();

	let submit = $state<HTMLElement | null>(null);

	function onkeydown(e: KeyboardEvent) {
		if (e.key !== 'Enter' || !(e.metaKey || e.ctrlKey) || submitting) return;
		e.preventDefault();
		submit?.closest('form')?.requestSubmit();
	}
</script>

<svelte:window {onkeydown} />

<!-- Submit comes first so Tab from the last field reaches it before Cancel -->
<div
	class="flex flex-col gap-3 border-t border-border pt-6 sm:flex-row-reverse sm:items-center sm:justify-between"
>
	<Button
		bind:ref={submit}
		type="submit"
		size="lg"
		class="w-full sm:w-auto"
		disabled={submitting}
		aria-busy={submitting}
		aria-keyshortcuts="Control+Enter Meta+Enter"
	>
		{#if submitting}<Spinner />{:else}<BanknoteArrowUp />{/if}
		{submitLabel}
	</Button>
	<Button variant="secondary" size="lg" href={cancelHref} class="w-full sm:w-auto">
		{$_('cancel')}
	</Button>
</div>
