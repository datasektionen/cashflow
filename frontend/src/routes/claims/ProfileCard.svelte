<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { api } from '#lib/api/index.ts';
	import type { BankInfo, User } from '#lib/api/types.ts';
	import { failed, success } from '#lib/stores/alerts.ts';
	import { Button, Card, Field, Input, Spinner } from '#lib/components/ui/index.ts';

	let { user }: { user: User } = $props();

	// Seeded once so a layout refresh doesn't clobber edits
	// svelte-ignore state_referenced_locally
	let bank = $state({ ...user.bank_info });
	let saving = $state(false);

	const dirty = $derived(
		Object.entries(bank).some(([k, v]) => v !== user.bank_info[k as keyof BankInfo])
	);

	async function save(e: SubmitEvent) {
		e.preventDefault();
		saving = true;
		try {
			const updated = await api.users.updateBankInfo({
				bank_name: bank.bank_name.trim(),
				sorting_number: bank.sorting_number.trim(),
				bank_account: bank.bank_account.trim()
			});
			user.bank_info = updated.bank_info;
			success($_('profile.bank_info_saved'));
		} catch (err) {
			failed(err, $_('profile.bank_info_save_failed'));
		} finally {
			saving = false;
		}
	}
</script>

<Card padded={false} class="px-4 py-3">
	<form onsubmit={save} class="grid grid-cols-2 items-end gap-3 sm:flex">
		<Field label={$_('profile.bank_name')} for="bank-name" class="col-span-2 sm:flex-1">
			<Input id="bank-name" type="text" maxlength={30} bind:value={bank.bank_name} />
		</Field>
		<Field label={$_('profile.sorting_number')} for="sorting-number" class="sm:w-36">
			<Input
				id="sorting-number"
				type="text"
				inputmode="numeric"
				maxlength={6}
				bind:value={bank.sorting_number}
			/>
		</Field>
		<Field label={$_('profile.bank_account')} for="bank-account" class="sm:flex-1">
			<Input
				id="bank-account"
				type="text"
				inputmode="numeric"
				maxlength={13}
				bind:value={bank.bank_account}
			/>
		</Field>
		<Button type="submit" disabled={saving || !dirty} class="col-span-2 min-w-20">
			{#if saving}
				<Spinner />
			{:else}
				{$_('save')}
			{/if}
		</Button>
	</form>
</Card>
