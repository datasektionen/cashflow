<script lang="ts">
	import type { PageProps } from './$types';
	import { _ } from 'svelte-i18n';
	import { api } from '#lib/api/index.ts';
	import { error, failed, success, warning } from '#lib/stores/alerts.ts';
	import { refreshAll, goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { Button, Card, ConfirmDialog } from '#lib/components/ui/index.ts';

	let { data }: PageProps = $props();

	// The OAuth start flow is a server-side browser redirect, not a fetch.
	const authUrl = '/fortnox/auth/';

	let disconnecting = $state(false);

	async function disconnect() {
		disconnecting = true;
		try {
			await api.fortnox.disconnect();
			warning($_('fortnox.disconnected'));
			await refreshAll();
		} catch (e) {
			failed(e, $_('action_failed'));
		} finally {
			disconnecting = false;
		}
	}

	// Surface the result of the OAuth redirect flow, then clean the query param.
	onMount(() => {
		const result = page.url.searchParams.get('fortnox');
		if (result === 'success') {
			success($_('fortnox.authenticated'));
		} else if (result === 'error') {
			error($_('fortnox.auth_failed'));
		}
		if (result) {
			goto('/admin/fortnox', { replaceState: true, reset: false });
		}
	});
</script>

<Card class="max-w-xl">
	<div class="flex flex-col gap-4">
		{#if data.status.is_connected}
			<p class="text-sm">
				{$_('fortnox.connected_by', { values: { name: data.status.authenticated_by } })}
			</p>
			<div class="flex flex-wrap gap-2">
				<Button href={authUrl}>{$_('fortnox.reauthenticate')}</Button>
				<ConfirmDialog
					title={$_('fortnox.disconnect')}
					confirmLabel={$_('fortnox.disconnect')}
					cancelLabel={$_('cancel')}
					danger
					onConfirm={disconnect}
				>
					{#snippet trigger({ props })}
						<Button variant="danger-outline" disabled={disconnecting} {...props}>
							{$_('fortnox.disconnect')}
						</Button>
					{/snippet}
				</ConfirmDialog>
			</div>
		{:else}
			<p class="text-sm text-muted-foreground">{$_('fortnox.not_connected')}</p>
			<Button href={authUrl} class="w-fit">{$_('fortnox.authenticate')}</Button>
		{/if}
	</div>
</Card>
