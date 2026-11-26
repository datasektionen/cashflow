<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { type Alert, dismiss } from '#lib/stores/alerts.ts';
	import { CircleAlert, CircleCheck, CircleX, X } from '@lucide/svelte';
	import { onMount } from 'svelte';
	import { Tween } from 'svelte/motion';
	import { linear } from 'svelte/easing';
	import { Button } from '#lib/components/ui/index.ts';

	let { alert }: { alert: Alert } = $props();

	const tones = {
		success: { icon: CircleCheck, color: 'text-primary-text' },
		warning: { icon: CircleAlert, color: 'text-warning-soft-foreground' },
		error: { icon: CircleX, color: 'text-danger-text' }
	};
	const tone = $derived(tones[alert.type]);

	const progress = new Tween(100, { duration: () => alert.duration, easing: linear });

	onMount(() => {
		progress.set(0);
		const timer = setTimeout(() => dismiss(alert.id), alert.duration);
		return () => clearTimeout(timer);
	});
</script>

<div
	role={alert.type === 'error' ? 'alert' : 'status'}
	class="relative flex w-80 max-w-[calc(100vw-2rem)] items-start gap-3 overflow-hidden border border-border bg-card p-4 pr-11 text-sm shadow-lg"
>
	<tone.icon class={['mt-px size-4 shrink-0', tone.color]} />
	<p class="flex-1">{alert.message}</p>
	<Button
		variant="ghost"
		size="icon-sm"
		onclick={() => dismiss(alert.id)}
		aria-label={$_('close')}
		class="absolute top-2.5 right-2 text-muted-foreground hover:text-foreground"
	>
		<X />
	</Button>
	<div
		class={['absolute bottom-0 left-0 h-0.5 bg-current', tone.color]}
		style="width: {progress.current}%"
	></div>
</div>
