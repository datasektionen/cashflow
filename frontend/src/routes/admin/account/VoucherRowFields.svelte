<script lang="ts" module>
	import type { ExpensePart, InvoicePart, VoucherRow } from '#lib/api/types.ts';
	import type { VoucherRowDraft } from './voucherRowValidation';
	import { add, isZero, toDecimal } from 'dinero.js';
	import { sumDinero, ZERO } from '#lib/money.ts';

	function emptyVoucherRow(): VoucherRowDraft {
		return {
			account: '',
			cost_centre: '',
			description: '',
			debit: ZERO,
			credit: ZERO
		};
	}

	/** One debit row per distinct account, cost centre and budget line, plus a balancing credit row. */
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
	import AmountInput from '#lib/components/AmountInput.svelte';
	import { Button } from '#lib/components/ui/index.ts';
	import AdvancedCombobox from '#lib/components/AdvancedCombobox.svelte';
	import type { ComboboxColumn } from '#lib/components/AdvancedCombobox.svelte';
	import { type Dinero } from 'dinero.js';
	import { formatDineroAmount } from '#lib/money.ts';
	import type { FortnoxAccount, FortnoxCostCentre } from '#lib/api/types.ts';
	import {
		type VoucherRowWarnings,
		VoucherRowField,
		voucherRowValidation
	} from './voucherRowValidation';

	type VoucherRowFieldsProps = {
		voucherRows: VoucherRowDraft[];
		accounts: FortnoxAccount[];
		costCentres: FortnoxCostCentre[];
		expectedTotal?: Dinero<number, 'SEK'>;
		warnings?: VoucherRowWarnings;
	};

	let {
		voucherRows = $bindable([]),
		accounts,
		costCentres,
		expectedTotal,
		warnings = $bindable({})
	}: VoucherRowFieldsProps = $props();

	// One line when wide; two (account, cost centre / debit, credit) when narrow
	const cols =
		'grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_2rem] @xl:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)_7rem_7rem_2rem]';
	// Keeps the last column on the first line when narrow
	const corner = '@max-xl:col-start-3 @max-xl:row-start-1';

	let validationResult = $state(voucherRowValidation.get());
	$effect(() => {
		const result = voucherRowValidation.run({
			voucherRowDrafts: voucherRows,
			expectedTotal
		});
		validationResult = result;
		warnings = result.getWarnings() as VoucherRowWarnings;
	});

	const totalDebit = $derived(sumDinero(voucherRows.map((row) => row.debit)));
	const totalCredit = $derived(sumDinero(voucherRows.map((row) => row.credit)));

	export function validate(): boolean {
		return validationResult.isValid();
	}

	// Undeletable rows go first; `i` stays the row's index in `voucherRows`
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
			field: 'number',
			render: AccountNumberSnippet
		},
		{
			field: 'description',
			render: AccountDescriptionSnippet
		}
	];

	const costCentreColumns: ComboboxColumn<FortnoxCostCentre>[] = [
		{
			field: 'code',
			render: CostCentreCodeSnippet
		},
		{
			field: 'description',
			render: CostCentreDescriptionSnippet
		}
	];
</script>

{#snippet AccountDisplay(account: FortnoxAccount)}
	<span class="font-mono">{account.number}</span>
	<span class="ml-2 truncate text-xs text-muted-foreground">{account.description}</span>
{/snippet}
{#snippet AccountNumberSnippet(account: FortnoxAccount)}
	<span class="font-mono">{account.number}</span>
{/snippet}
{#snippet AccountDescriptionSnippet(account: FortnoxAccount)}
	<span>{account.description}</span>
{/snippet}

{#snippet CostCentreDisplay(costCentre: FortnoxCostCentre)}
	<span>{costCentre.code}</span>
	<span class="ml-2 truncate text-xs text-muted-foreground">{costCentre.description}</span>
{/snippet}
{#snippet CostCentreCodeSnippet(costCentre: FortnoxCostCentre)}
	<span>{costCentre.code}</span>
{/snippet}
{#snippet CostCentreDescriptionSnippet(costCentre: FortnoxCostCentre)}
	<span>{costCentre.description}</span>
{/snippet}

<div class="flex flex-col gap-2">
	<div class="@container">
		<div class="flex flex-col gap-4 @xl:gap-2">
			<div class="{cols} gap-x-3 gap-y-1 text-sm font-medium">
				<div>{$_('booking_account_code')}</div>
				<div>{$_('booking_cost_centre')}</div>
				<div class="text-right">{$_('booking_debit')}</div>
				<div class="text-right">{$_('booking_credit')}</div>
				<div class={corner}></div>
			</div>

			{#each orderedRows as { row, i } (i)}
				<div class="{cols} items-center gap-x-3 gap-y-2">
					<AdvancedCombobox
						name="account-{i}"
						label={$_('booking_account_code')}
						class="min-w-18 text-sm"
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
						label={$_('booking_cost_centre')}
						class="text-sm"
						columns={costCentreColumns}
						items={costCentres}
						searchField={['code', 'description']}
						valueField="code"
						bind:value={row.cost_centre}
						display={CostCentreDisplay}
						locked={row.lockedFields?.includes('cost_centre')}
					/>

					<AmountInput
						label={$_('booking_debit')}
						bind:value={() => row.debit, (v) => (row.debit = v ?? ZERO)}
						locked={!isZero(row.credit) || row.lockedFields?.includes('debit')}
					/>
					<AmountInput
						label={$_('booking_credit')}
						bind:value={() => row.credit, (v) => (row.credit = v ?? ZERO)}
						locked={!isZero(row.debit) || row.lockedFields?.includes('credit')}
					/>
					{#if row.deletable === false}
						<div class={corner}></div>
					{:else}
						<Button
							variant="ghost"
							size="icon-sm"
							class="text-muted-foreground {corner}"
							aria-label={$_('remove')}
							onclick={() => removeRow(i)}
						>
							<X />
						</Button>
					{/if}
				</div>
			{/each}

			<Button
				variant="ghost"
				size="sm"
				class="w-fit text-muted-foreground"
				onclick={() => voucherRows.push(emptyVoucherRow())}
			>
				<Plus />
				{$_('booking_add_row')}
			</Button>

			<div
				class="{cols} gap-x-3 gap-y-1 border-t border-border pt-3 text-sm font-medium tabular-nums"
			>
				<div class="@max-xl:hidden"></div>
				<div class="text-muted-foreground @max-xl:col-span-3 @xl:text-right">{$_('total')}</div>
				<div class="border-x border-transparent px-3 text-right">
					{formatDineroAmount(totalDebit)}
				</div>
				<div class="border-x border-transparent px-3 text-right">
					{formatDineroAmount(totalCredit)}
				</div>
				<div class="@max-xl:hidden"></div>
			</div>
		</div>
	</div>

	{#if validationResult.hasErrors(VoucherRowField.DebitCredit) || validationResult.hasWarnings(VoucherRowField.ExpectedTotal)}
		<div class="flex flex-col items-end gap-1 text-xs font-medium">
			{#if validationResult.hasErrors(VoucherRowField.DebitCredit)}
				<p class="flex items-center gap-1.5 text-danger-text">
					<CircleAlert class="size-3.5" />
					{$_('booking_debit_credit_mismatch')}
				</p>
			{/if}
			{#if validationResult.hasWarnings(VoucherRowField.ExpectedTotal)}
				<p class="flex items-center gap-1.5 text-warning-soft-foreground">
					<TriangleAlert class="size-3.5" />
					{$_('booking_total_mismatch', {
						values: { total: formatDineroAmount(expectedTotal!) }
					})}
				</p>
			{/if}
		</div>
	{/if}
</div>
