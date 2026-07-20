<script lang="ts">
	import type { PageProps } from './$types';
	import { _ } from 'svelte-i18n';
	import { api } from '$lib/api';
	import { isErrorResponse } from '$lib/api/errors';
	import { alerts, error, success, warning } from '$lib/stores/alerts';
	import { invalidateAll, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';

	let { data }: PageProps = $props();

	// The OAuth start flow is a server-side browser redirect, not a fetch.
	const authUrl = '/fortnox/auth/';

	let disconnecting = $state(false);

	async function disconnect() {
		disconnecting = true;
		try {
			await api.fortnox.disconnect();
			alerts.update((a) => [...a, warning($_('fortnox.disconnected'))]);
			await invalidateAll();
		} catch (e) {
			if (isErrorResponse(e)) {
				alerts.update((a) => [...a, error(e.detail)]);
			} else {
				alerts.update((a) => [...a, error($_('action_failed'))]);
			}
		} finally {
			disconnecting = false;
		}
	}

	// Surface the result of the OAuth redirect flow, then clean the query param.
	onMount(() => {
		const result = page.url.searchParams.get('fortnox');
		if (result === 'success') {
			alerts.update((a) => [...a, success($_('fortnox.authenticated'))]);
		} else if (result === 'error') {
			alerts.update((a) => [...a, error($_('fortnox.auth_failed'))]);
		}
		if (result) {
			goto('/admin/fortnox', { replaceState: true, noScroll: true });
		}
	});
</script>

<div class="flex max-w-xl flex-col gap-4">
	{#if data.status.is_connected}
		<p class="text-sm text-base-text dark:text-dark-base-text">
			{$_('fortnox.connected_by', { values: { name: data.status.authenticated_by } })}
		</p>
		<div class="flex gap-2">
			<a
				href={authUrl}
				class="bg-money-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-money-green-700 dark:bg-money-green-500 dark:hover:bg-money-green-600"
			>
				{$_('fortnox.reauthenticate')}
			</a>
			<button
				type="button"
				onclick={disconnect}
				disabled={disconnecting}
				class="border border-base-400 px-4 py-2 text-sm font-medium text-base-text transition-colors hover:bg-base-300 disabled:opacity-50 dark:border-dark-base-200 dark:text-dark-base-text dark:hover:bg-dark-base-200"
			>
				{$_('fortnox.disconnect')}
			</button>
		</div>
	{:else}
		<p class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('fortnox.not_connected')}
		</p>
		<a
			href={authUrl}
			class="w-fit bg-money-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-money-green-700 dark:bg-money-green-500 dark:hover:bg-money-green-600"
		>
			{$_('fortnox.authenticate')}
		</a>
	{/if}
</div>
