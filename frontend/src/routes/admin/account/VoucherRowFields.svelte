<script lang="ts" module>
	import type { ExpensePart, InvoicePart, VoucherRow } from '$lib/api/types';
	import type { VoucherRowDraft } from './voucherRowValidation';
	import { add, isZero, toDecimal } from 'dinero.js';
	import { sumDinero, ZERO } from '$lib/money';

	function emptyVoucherRow(): VoucherRowDraft {
		return {
			account: '',
			cost_centre: '',
			description: '',
			debit: ZERO,
			credit: ZERO
		};
	}

	/**
	 * Prefills voucher rows from claim parts: one debit row per part from the
	 * account and cost centre GOrdian/Fortnox recommend, plus a balancing row
	 * crediting `creditAccount` (the claim's recommended liability account).
	 * Parts that resolve to an identical row (same account, cost centre and
	 * budget line) are merged into one row with their amounts summed; parts
	 * without a resolved account stay separate.
	 */
	export function draftsFromParts(
		parts: (ExpensePart | InvoicePart)[],
		creditAccount: number | null
	): VoucherRowDraft[] {
		if (parts.length === 0) return [emptyVoucherRow()];

		const rows: VoucherRowDraft[] = [];
		const mergeable = new Map<string, VoucherRowDraft>();
		for (const part of parts) {
			const account = part.recommended_accounts?.[0];
			const row = emptyVoucherRow();
			if (account != null) row.account = String(account);
			row.cost_centre = part.recommended_cost_centre ?? '';
			row.description = part.budget_line;
			row.debit = part.amount;

			const key = `${row.account}\0${row.cost_centre}\0${row.description}`;
			const existing = account != null ? mergeable.get(key) : undefined;
			if (existing) {
				existing.debit = add(existing.debit, row.debit);
			} else {
				if (account != null) mergeable.set(key, row);
				rows.push(row);
			}
		}

		const balancing = emptyVoucherRow();
		if (creditAccount != null) balancing.account = String(creditAccount);
		balancing.credit = sumDinero(parts.map((p) => p.amount));
		return [...rows, balancing];
	}

	export function toVoucherRows(drafts: VoucherRowDraft[]): VoucherRow[] {
		return drafts
			.filter((d) => d.account !== '')
			.map((d) => ({
				account: Number(d.account),
				cost_centre: d.cost_centre || undefined,
				description: d.description || undefined,
				debit: isZero(d.debit) ? undefined : toDecimal(d.debit),
				credit: isZero(d.credit) ? undefined : toDecimal(d.credit)
			}));
	}
</script>

<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { CircleAlert, Plus, X, TriangleAlert } from '@lucide/svelte';
	import AmountInput from '$lib/components/AmountInput.svelte';
	import AdvancedCombobox from '$lib/components/AdvancedCombobox.svelte';
	import type { ComboboxColumn } from '$lib/components/AdvancedCombobox.svelte';
	import { type Dinero } from 'dinero.js';
	import { formatDineroAmount } from '$lib/money';
	import type { FortnoxAccount, FortnoxCostCentre } from '$lib/api/types';
	import {
		type VoucherRowErrors,
		type VoucherRowWarnings,
		VoucherRowField,
		voucherRowValidation
	} from './voucherRowValidation';

	type VoucherRowFieldsProps = {
		voucherRows: VoucherRowDraft[];
		accounts: FortnoxAccount[];
		costCentres: FortnoxCostCentre[];
		expectedTotal?: Dinero<number, 'SEK'>;
		errors?: VoucherRowErrors;
		warnings?: VoucherRowWarnings;
	};

	let {
		voucherRows = $bindable([]),
		accounts,
		costCentres,
		expectedTotal,
		errors = $bindable({}),
		warnings = $bindable({})
	}: VoucherRowFieldsProps = $props();

	const cols = 'grid-cols-[1fr_18rem_8rem_8rem_2rem]';

	let validationResult = $state(voucherRowValidation.get());
	$effect(() => {
		const result = voucherRowValidation.run({
			voucherRowDrafts: voucherRows,
			expectedTotal
		});
		validationResult = result;
		errors = result.getErrors() as VoucherRowErrors;
		warnings = result.getWarnings() as VoucherRowWarnings;
	});

	const totalDebit = $derived(sumDinero(voucherRows.map((row) => row.debit)));
	const totalCredit = $derived(sumDinero(voucherRows.map((row) => row.credit)));

	let attemptedSubmit = $state(false);

	export function validate(): boolean {
		attemptedSubmit = true;
		return validationResult.isValid();
	}

	// Undeletable rows (e.g. a mandatory balancing row) are pinned above the
	// rest; `i` keeps pointing at the row's real position in `voucherRows` so
	// binding and removal stay correct after reordering.
	const orderedRows = $derived(
		voucherRows
			.map((row, i) => ({ row, i }))
			.sort((a, b) => Number(b.row.deletable === false) - Number(a.row.deletable === false))
	);

	function removeRow(i: number) {
		voucherRows = voucherRows.filter((_, idx) => idx !== i);
	}

	const accountColumns: ComboboxColumn<FortnoxAccount>[] = [
		{
			label: 'Konto',
			field: 'number',
			render: AccountNumberSnippet
		},
		{
			label: 'Beskrivning',
			field: 'description',
			render: AccountDescriptionSnippet
		}
	];

	const costCentreColumns: ComboboxColumn<FortnoxCostCentre>[] = [
		{
			label: 'Kod',
			field: 'code',
			render: CostCentreCodeSnippet
		},
		{
			label: 'Beskrivning',
			field: 'description',
			render: CostCentreDescriptionSnippet
		}
	];
</script>

{#snippet AccountDisplay(account: FortnoxAccount)}
	<span>{account.number}</span>
	<span class="dark:dark-base-subtle ml-2 text-xs font-medium text-base-subtle uppercase">
		{account.description}
	</span>
{/snippet}
{#snippet AccountNumberSnippet(account: FortnoxAccount)}
	<span>{account.number}</span>
{/snippet}
{#snippet AccountDescriptionSnippet(account: FortnoxAccount)}
	<span>{account.description}</span>
{/snippet}

{#snippet CostCentreDisplay(costCentre: FortnoxCostCentre)}
	<span>{costCentre.code}</span>
	<span class="dark:dark-base-subtle ml-2 text-xs font-medium text-base-subtle uppercase">
		{costCentre.description}
	</span>
{/snippet}
{#snippet CostCentreCodeSnippet(costCentre: FortnoxCostCentre)}
	<span>{costCentre.code}</span>
{/snippet}
{#snippet CostCentreDescriptionSnippet(costCentre: FortnoxCostCentre)}
	<span>{costCentre.description}</span>
{/snippet}

<div class="flex flex-col">
	<!-- The 5-column ledger grid is wider than the narrow mobile card, so it
         scrolls horizontally on small screens (combobox dropdowns are portaled,
         so they aren't clipped by the scroll container). -->
	<div class="overflow-x-auto">
		<div class="min-w-max md:min-w-0">
			<div
				class="grid {cols} gap-x-4 text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
			>
				<div>{$_('booking_account_code')}</div>
				<div>{$_('booking_cost_centre')}</div>
				<div class="px-2 text-right">{$_('booking_debit')}</div>
				<div class="px-2 text-right">{$_('booking_credit')}</div>
				<div></div>
			</div>

			{#each orderedRows as { row, i } (i)}
				<div
					class="grid {cols} items-center gap-x-2 border-b border-base-400 py-1 md:gap-x-4 dark:border-dark-base-200"
				>
					<AdvancedCombobox
						name="account-{i}"
						class="min-w-18 text-sm lg:min-w-42"
						columns={accountColumns}
						items={accounts}
						searchField={['number', 'description']}
						valueField="number"
						bind:value={row.account}
						display={AccountDisplay}
						locked={row.lockedFields?.includes('account')}
					/>

					<AdvancedCombobox
						name="cost-centre-{i}"
						class="text-sm"
						columns={costCentreColumns}
						items={costCentres}
						searchField={['code', 'description']}
						valueField="code"
						bind:value={row.cost_centre}
						display={CostCentreDisplay}
						locked={row.lockedFields?.includes('cost_centre')}
					/>

					<div
						class="flex border border-base-500 bg-base-200 dark:border-dark-base-200 dark:bg-dark-base-200"
					>
						<AmountInput
							bind:value={() => row.debit, (v) => (row.debit = v ?? ZERO)}
							class="text-sm"
							locked={!isZero(row.credit) || row.lockedFields?.includes('debit')}
						/>
					</div>
					<div
						class="flex border border-base-500 bg-base-200 dark:border-dark-base-200 dark:bg-dark-base-200"
					>
						<AmountInput
							bind:value={() => row.credit, (v) => (row.credit = v ?? ZERO)}
							class="text-sm"
							locked={!isZero(row.debit) || row.lockedFields?.includes('credit')}
						/>
					</div>
					{#if row.deletable === false}
						<div></div>
					{:else}
						<button
							type="button"
							onclick={() => removeRow(i)}
							class="cursor-pointer text-base-subtle dark:text-dark-base-subtle"
						>
							<X class="size-4 transition-all hover:scale-125" />
						</button>
					{/if}
				</div>
			{/each}

			<button
				type="button"
				onclick={() => voucherRows.push(emptyVoucherRow())}
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
				<div class="px-2 text-right tabular-nums">{formatDineroAmount(totalDebit)}</div>
				<div class="px-2 text-right tabular-nums">{formatDineroAmount(totalCredit)}</div>
				<div></div>
			</div>
		</div>
	</div>

	<div class="mt-2 flex flex-col items-end gap-1">
		{#if validationResult.hasErrors(VoucherRowField.DebitCredit)}
			<span
				class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-red-500 uppercase"
			>
				<span>{$_('booking_debit_credit_mismatch')}</span>
				<CircleAlert class="size-4" />
			</span>
		{/if}
		{#if validationResult.hasWarnings(VoucherRowField.ExpectedTotal)}
			<span
				class="flex flex-row items-center gap-1 text-[8pt] font-medium tracking-wide text-yellow-500 uppercase"
			>
				<span
					>{$_('booking_total_mismatch', {
						values: { total: formatDineroAmount(expectedTotal!) }
					})}</span
				>
				<TriangleAlert class="size-4" />
			</span>
		{/if}
	</div>
</div>
