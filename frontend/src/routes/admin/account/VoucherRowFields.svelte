<script lang="ts" module>
	import type { VoucherRow } from '$lib/api/types.ts';

	export type VoucherRowDraft = {
		// Account code as a string (the AdvancedCombobox value), e.g. "1234".
		account: string;
		cost_centre: string;
		description: string;
		debit: number | null;
		credit: number | null;
	};

	export function newVoucherRow(): VoucherRowDraft {
		return {
			account: '',
			cost_centre: '',
			description: '',
			debit: null,
			credit: null
		};
	}

	export function toVoucherRows(drafts: VoucherRowDraft[]): VoucherRow[] {
		return drafts
			.filter((d) => d.account !== '')
			.map((d) => ({
				account: Number(d.account),
				cost_centre: d.cost_centre || undefined,
				description: d.description || undefined,
				debit: d.debit ?? undefined,
				credit: d.credit ?? undefined
			}));
	}
</script>

<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Plus, X } from '@lucide/svelte';
	import ComboBox from '$lib/components/ComboBox.svelte';
	import AmountInput from '$lib/components/AmountInput.svelte';
	import AdvancedCombobox from '$lib/components/AdvancedCombobox.svelte';
	import type { ComboboxColumn } from '$lib/components/AdvancedCombobox.svelte';

	type VoucherRowFieldsProps = {
		voucherRows: VoucherRowDraft[];
	};

	let { voucherRows = $bindable([]) }: VoucherRowFieldsProps = $props();

	const cols = 'grid-cols-[1fr_18rem_8rem_8rem_2rem]';

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});

	const totalDebit = $derived(voucherRows.reduce((sum, r) => sum + (r.debit ?? 0), 0));
	const totalCredit = $derived(voucherRows.reduce((sum, r) => sum + (r.credit ?? 0), 0));

	function removeRow(i: number) {
		voucherRows = voucherRows.filter((_, idx) => idx !== i);
	}

	type Account = {
		code: number;
		description: string;
	};

	// Placeholder
	const accounts: Account[] = [
		{
			code: 1234,
			description: 'Sektionslokalsgruppen'
		},
		{
			code: 5678,
			description: 'Näringslivsgruppen'
		}
	];

	const columns: ComboboxColumn<Account>[] = [
		{
			label: 'Konto',
			field: 'code',
			render: CodeSnippet
		},
		{
			label: 'Beskrivning',
			field: 'description',
			render: DescriptionSnippet
		}
	];
</script>

{#snippet AccountDisplay(account: Account)}
	<span>{account.code}</span>
	<span class="dark:dark-base-subtle ml-2 text-xs font-medium text-base-subtle uppercase">
		{account.description}
	</span>
{/snippet}
{#snippet CodeSnippet(account: Account)}
	<span>{account.code}</span>
{/snippet}
{#snippet DescriptionSnippet(account: Account)}
	<span>{account.description}</span>
{/snippet}

<div class="flex flex-col">
	<div
		class="grid {cols} gap-x-4 text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
	>
		<div>{$_('booking_account_code')}</div>
		<div>{$_('booking_cost_centre')}</div>
		<div class="px-2 text-right">{$_('booking_debit')}</div>
		<div class="px-2 text-right">{$_('booking_credit')}</div>
		<div></div>
	</div>

	{#each voucherRows as row, i (i)}
		<div
			class="grid {cols} items-center gap-x-4 border-b border-base-400 py-1 dark:border-dark-base-200"
		>
			<AdvancedCombobox
				name="account-{i}"
				class="text-sm"
				{columns}
				items={accounts}
				searchField={['code', 'description']}
				valueField="code"
				bind:value={row.account}
				display={AccountDisplay}
			/>

			<AdvancedCombobox
				name="account-{i}"
				class="text-sm"
				{columns}
				items={accounts}
				searchField={['code', 'description']}
				valueField="code"
				bind:value={row.cost_centre}
				display={AccountDisplay}
			/>

			<div
				class="flex border border-base-500 bg-base-200 dark:border-dark-base-200 dark:bg-dark-base-200"
			>
				<AmountInput bind:value={row.debit} class="text-sm" />
			</div>
			<div
				class="flex border border-base-500 bg-base-200 dark:border-dark-base-200 dark:bg-dark-base-200"
			>
				<AmountInput bind:value={row.credit} class="text-sm" />
			</div>
			<button
				type="button"
				onclick={() => removeRow(i)}
				class="cursor-pointer text-base-subtle dark:text-dark-base-subtle"
			>
				<X class="size-4 transition-all hover:scale-125" />
			</button>
		</div>
	{/each}

	<button
		type="button"
		onclick={() => voucherRows.push(newVoucherRow())}
		class="mt-1 flex w-fit cursor-pointer items-center gap-1 py-1 text-sm font-medium text-base-subtle transition-colors hover:text-base-text dark:text-dark-base-subtle dark:hover:text-dark-base-text"
	>
		<Plus class="size-4" />
		<span>{$_('booking_add_row')}</span>
	</button>

	<div
		class="mt-2 grid {cols} gap-x-4 border-t border-base-400 pt-2 text-sm font-medium dark:border-dark-base-200"
	>
		<div></div>
		<div class="text-right text-xs text-base-subtle uppercase dark:text-dark-base-subtle">
			{$_('total')}
		</div>
		<div class="px-2 text-right tabular-nums">{fmt.format(totalDebit)}</div>
		<div class="px-2 text-right tabular-nums">{fmt.format(totalCredit)}</div>
		<div></div>
	</div>
</div>
