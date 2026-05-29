<script lang="ts">
	import { type Alert, AlertType, dismiss } from '$lib/stores/alerts';
	import { CircleAlert, CircleDollarSign, CircleX, Lightbulb, X } from '@lucide/svelte';
	import { logger } from '$lib/logger';
	import { onMount } from 'svelte';
	import { Tween } from 'svelte/motion';
	import { linear } from 'svelte/easing';

	type AlertProps = {
		alert: Alert;
	};

	let { alert }: AlertProps = $props();
	const colors = $derived.by(() => {
		switch (alert.type) {
			case AlertType.Success:
				return 'money-green';
			case AlertType.Warning:
				return 'amber';
			case AlertType.Info:
				return 'secondary';
			case AlertType.Error:
				return 'red';
		}
	});

	function handleDismiss(): void {
		logger.debug('dismiss');
		console.log('test');
		dismiss(alert.id);
	}

	const progress = new Tween(100, { duration: alert.duration, easing: linear });

	onMount(() => {
		progress.set(0);
		const timer = setTimeout(() => dismiss(alert.id), alert.duration);
		return () => clearTimeout(timer);
	});
</script>

<div
	class={[
		'relative flex h-20 w-64 flex-row items-center justify-between bg-base-400 p-4 shadow-xl dark:bg-dark-base-150'
	]}
>
	{#if alert.type === AlertType.Success}
		<CircleDollarSign class="mr-2 shrink-0 text-money-green-500" />
	{:else if alert.type === AlertType.Warning}
		<CircleAlert class="mr-2 shrink-0 text-amber-500" />
	{:else if alert.type === AlertType.Error}
		<CircleX class="mr-2 shrink-0 text-red-500" />
	{:else if alert.type === AlertType.Info}
		<Lightbulb class="mr-2 shrink-0 text-secondary-500" />
	{/if}
	<div class="flex-1 text-base text-base-subtle dark:text-dark-base-subtle">
		{alert.message}
	</div>
	<div class="shrink-0">
		<button
			class={['cursor-pointer text-base-subtle dark:text-dark-base-subtle']}
			onclick={handleDismiss}
		>
			<X class="transition-all hover:scale-110" />
		</button>
	</div>

	<div
		class={`absolute bottom-0 left-0 h-1 bg-${colors}-500`}
		style="width: {progress.current}%"
	></div>
</div>
