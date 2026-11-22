<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Trash2 } from '@lucide/svelte';
	import { goto } from '$app/navigation';
	import { api } from '#lib/api/index.ts';
	import type { Expense, Invoice } from '#lib/api/types.ts';
	import { failed, success } from '#lib/stores/alerts.ts';
	import { Button, ConfirmDialog, Spinner } from '#lib/components/ui/index.ts';

	let {
		kind,
		claim,
		redirect
	}: {
		kind: 'expense' | 'invoice';
		claim: Expense | Invoice;
		redirect: string;
	} = $props();

	let pending = $state(false);

	async function handleDelete() {
		pending = true;
		await api[`${kind}s`]
			.delete(claim.id)
			.then(() => {
				success($_(`alerts.${kind}_delete`, { values: { description: claim.description } }));
				goto(redirect);
			})
			.catch((e) => failed(e, $_('action_failed')))
			.finally(() => (pending = false));
	}
</script>

<ConfirmDialog
	title={$_(`${kind}_delete_confirm_title`)}
	description={$_(`${kind}_delete_confirm_description`)}
	confirmLabel={$_(`${kind}_delete_confirm_action`)}
	cancelLabel={$_('cancel')}
	danger
	onConfirm={handleDelete}
>
	{#snippet trigger({ props })}
		<Button
			variant="danger-outline"
			size="icon"
			aria-label={$_(`${kind}_delete_confirm_title`)}
			disabled={pending}
			{...props}
		>
			{#if pending}<Spinner />{:else}<Trash2 />{/if}
		</Button>
	{/snippet}
</ConfirmDialog>
