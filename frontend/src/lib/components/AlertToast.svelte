<script lang="ts">
	import { type Alert, AlertType, dismiss } from '$lib/stores/alerts';
	import { X } from '@lucide/svelte';
	import { logger } from '$lib/logger.ts';
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
	class={['relative flex h-20 w-64 flex-row justify-between bg-base-400 p-4 dark:bg-dark-base-150']}
>
	<span class="text-base-text dark:text-dark-base-text">{alert.message}</span>
	<button
		class={['absolute top-2 right-2 cursor-pointer text-base-text dark:text-dark-base-text']}
		onclick={handleDismiss}
	>
		<X class="transition-all hover:scale-110" />
	</button>
	<div
		class={`absolute bottom-0 left-0 h-1 bg-${colors}-500`}
		style="width: {progress.current}%"
	></div>
</div>
