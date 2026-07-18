<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { api } from '$lib/api';
	import { isErrorResponse } from '$lib/api/errors';
	import type { User } from '$lib/api/types';
	import { alerts, error, success } from '$lib/stores/alerts';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import UserAvatar from '$lib/components/UserAvatar.svelte';

	let { user }: { user: User } = $props();

	// Form state is seeded once from the loaded user; edits must not be
	// clobbered if the layout data refreshes.
	// svelte-ignore state_referenced_locally
	let bankName = $state(user.bank_info.bank_name);
	// svelte-ignore state_referenced_locally
	let sortingNumber = $state(user.bank_info.sorting_number);
	// svelte-ignore state_referenced_locally
	let bankAccount = $state(user.bank_info.bank_account);
	let saving = $state(false);

	const dirty = $derived(
		bankName !== user.bank_info.bank_name ||
			sortingNumber !== user.bank_info.sorting_number ||
			bankAccount !== user.bank_info.bank_account
	);

	async function save(e: SubmitEvent) {
		e.preventDefault();
		saving = true;
		try {
			const updated = await api.users.updateBankInfo({
				bank_name: bankName.trim(),
				sorting_number: sortingNumber.trim(),
				bank_account: bankAccount.trim()
			});
			user.bank_info = updated.bank_info;
			alerts.update((a) => [...a, success($_('profile.bank_info_saved'))]);
		} catch (err) {
			const message = isErrorResponse(err) ? err.detail : $_('profile.bank_info_save_failed');
			alerts.update((a) => [...a, error(message)]);
		} finally {
			saving = false;
		}
	}

	const inputClass =
		'border border-base-500 bg-base-200 p-2 text-sm placeholder:text-base-subtle ' +
		'dark:border-dark-base-200 dark:bg-dark-base-200 dark:placeholder:text-dark-base-subtle';
</script>

<div
	class="mb-6 flex flex-wrap items-center gap-6 border border-base-400 p-4 dark:border-dark-base-200"
>
	<div class="flex items-center gap-4">
		<UserAvatar username={user.username} class="size-16" />
		<div>
			<div class="font-semibold">{user.first_name} {user.last_name}</div>
			<div class="text-sm text-base-subtle dark:text-dark-base-subtle">{user.email}</div>
		</div>
	</div>

	<form onsubmit={save} class="flex flex-wrap items-end gap-3">
		<label
			class="flex flex-col gap-1 text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
		>
			{$_('profile.bank_name')}
			<input
				type="text"
				maxlength="30"
				bind:value={bankName}
				class="{inputClass} w-40 normal-case"
			/>
		</label>
		<label
			class="flex flex-col gap-1 text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
		>
			{$_('profile.sorting_number')}
			<input
				type="text"
				inputmode="numeric"
				maxlength="6"
				bind:value={sortingNumber}
				class="{inputClass} w-28 normal-case"
			/>
		</label>
		<label
			class="flex flex-col gap-1 text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
		>
			{$_('profile.bank_account')}
			<input
				type="text"
				inputmode="numeric"
				maxlength="13"
				bind:value={bankAccount}
				class="{inputClass} w-40 normal-case"
			/>
		</label>
		<button
			type="submit"
			disabled={saving || !dirty}
			class="flex min-w-24 cursor-pointer justify-center bg-money-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-money-green-500 disabled:cursor-not-allowed disabled:opacity-50"
		>
			{#if saving}
				<CashSpinner class="size-5" />
			{:else}
				{$_('save')}
			{/if}
		</button>
	</form>
</div>
