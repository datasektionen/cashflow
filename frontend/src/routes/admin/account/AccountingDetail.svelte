<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { getRedirect } from '#lib/stores/state.svelte.ts';
	import { api } from '#lib/api/index.ts';
	import { mayAccount } from '#lib/auth.ts';
	import type {
		AccountPayload,
		Expense,
		FortnoxAccount,
		FortnoxCostCentre,
		Invoice,
		User
	} from '#lib/api/types.ts';
	import { failed, success } from '#lib/stores/alerts.ts';
	import { claimTotal } from '#lib/money.ts';
	import PartsTable from '#lib/components/PartsTable.svelte';
	import ClaimDetailLayout from '#lib/components/claim/ClaimDetailLayout.svelte';
	import ClaimInfo from '#lib/components/claim/ClaimInfo.svelte';
	import CommentsCard from '#lib/components/claim/CommentsCard.svelte';
	import {
		Button,
		Card,
		ConfirmDialog,
		CopyableValue,
		Field,
		Input,
		Spinner
	} from '#lib/components/ui/index.ts';
	import VoucherRowFields, { draftsFromParts, toVoucherRows } from './VoucherRowFields.svelte';
	import {
		ValidationError,
		VoucherRowField,
		type VoucherRowDraft,
		type VoucherRowWarnings
	} from './voucherRowValidation';
	import { voucherValidation, VoucherFormField, type VoucherNumberErrors } from './validation';

	type Props = {
		kind: 'expense' | 'invoice';
		claim: Expense | Invoice;
		accounts: FortnoxAccount[];
		costCentres: FortnoxCostCentre[];
		user: User | null | undefined;
	};

	let { kind, claim, accounts, costCentres, user }: Props = $props();

	const expectedTotal = $derived(claimTotal(claim));
	const isAccounted = $derived(claim.voucher != null);
	// svelte-ignore state_referenced_locally
	let comments = $state(claim.comments);

	let voucherRowFields: VoucherRowFields | undefined = $state();
	let voucherRowWarnings: VoucherRowWarnings = $state({});

	// Prefill once; the form must not reset if data refreshes while editing.
	// svelte-ignore state_referenced_locally
	const drafts = draftsFromParts(claim.parts, claim.recommended_credit_account);
	// The last draft is the balancing credit row. Invoices keep its account editable.
	// svelte-ignore state_referenced_locally
	if (claim.parts.length > 0) {
		const balancing = drafts[drafts.length - 1];
		balancing.lockedFields =
			kind === 'expense'
				? ['account', 'cost_centre', 'debit', 'credit']
				: ['cost_centre', 'debit', 'credit'];
		balancing.deletable = false;
	}
	let voucherRows = $state<VoucherRowDraft[]>(drafts);
	let voucherNumber = $state('');
	let submitting = $state<'rows' | 'number' | null>(null);

	let voucherFormData = $state({
		// svelte-ignore state_referenced_locally
		description: claim.description
	});

	let voucherFormResult = $state(voucherValidation.get());
	const voucherFormErrors = $derived(voucherFormResult.getErrors() as VoucherNumberErrors);
	const descriptionError = $derived(
		voucherFormResult.isTested(VoucherFormField.Description)
			? voucherFormErrors[VoucherFormField.Description]?.[0]
			: undefined
	);

	function validateVoucherForm(field?: string) {
		voucherFormResult = voucherValidation.run(voucherFormData, field);
	}

	const voucherRowsPayload = () => ({
		voucher_rows: toVoucherRows(voucherRows),
		voucher_description: voucherFormData.description.trim()
	});

	// Back to the list it was opened from (keeping its filters), else the full queue
	function backToList() {
		const redirect = getRedirect();
		const id = page.url.searchParams.get('redirect');
		if (redirect.url && id != null && redirect.id === id) {
			redirect.url.searchParams.delete('redirect');
			return redirect.url;
		}
		return `/admin/account/${kind}s`;
	}

	async function submitAccounting(mode: 'rows' | 'number', payload: AccountPayload) {
		submitting = mode;
		try {
			const resource = kind === 'expense' ? api.expenses : api.invoices;
			const updated = await resource.account(claim.id, payload);
			success($_('admin_account.success', { values: { verification: updated.voucher } }));
			await goto(backToList());
		} catch (e) {
			failed(e, $_('admin_account.error'));
		} finally {
			submitting = null;
		}
	}

	let showSubmitDialog = $state(false);

	const hasVoucherRowWarnings = $derived(
		Object.values(voucherRowWarnings).some((messages) => messages.length > 0)
	);

	function submitVoucherRows() {
		// Validate both so all errors show at once, not one form at a time.
		const rowsValid = voucherRowFields?.validate() ?? false;
		validateVoucherForm();
		if (!rowsValid || voucherFormResult.hasErrors()) return;

		if (hasVoucherRowWarnings) {
			showSubmitDialog = true;
			return;
		}
		submitAccounting('rows', voucherRowsPayload());
	}

	// Rows without an account are dropped on submit, so require at least one.
	const hasSubmittableRows = $derived(toVoucherRows(voucherRows).length > 0);
</script>

<ConfirmDialog
	bind:open={showSubmitDialog}
	title={$_('confirm_account_dialog')}
	description={voucherRowWarnings[VoucherRowField.ExpectedTotal]?.includes(
		ValidationError.DebitTotalMismatch
	)
		? $_('debit_total_mismatch_dialog')
		: undefined}
	confirmLabel={$_('confirm')}
	cancelLabel={$_('cancel')}
	onConfirm={() => submitAccounting('rows', voucherRowsPayload())}
/>

<ClaimDetailLayout {claim}>
	<Card
		title={$_('admin_account.create_voucher')}
		description={$_('admin_account.create_voucher_help')}
	>
		<form class="flex flex-col gap-6" onsubmit={(e) => e.preventDefault()}>
			<Field
				label={$_('admin_account.voucher_description')}
				for="voucher-description"
				error={descriptionError ? $_(descriptionError) : undefined}
			>
				<div class="flex">
					<span
						class="flex items-center border border-r-0 border-input bg-muted px-3 text-sm text-muted-foreground tabular-nums"
					>
						({claim.id})
					</span>
					<Input
						id="voucher-description"
						bind:value={voucherFormData.description}
						oninput={() => validateVoucherForm(VoucherFormField.Description)}
						aria-invalid={descriptionError != null}
					/>
				</div>
			</Field>

			<VoucherRowFields
				bind:this={voucherRowFields}
				bind:voucherRows
				{accounts}
				{costCentres}
				{expectedTotal}
				bind:warnings={voucherRowWarnings}
			/>

			<div class="flex justify-end">
				<Button
					class="min-w-24"
					onclick={submitVoucherRows}
					disabled={submitting != null || isAccounted || !hasSubmittableRows || !mayAccount(user)}
				>
					{#if submitting === 'rows'}<Spinner />{:else}{$_('submit')}{/if}
				</Button>
			</div>
		</form>
	</Card>

	<Card
		title={$_('admin_account.manual_accounting')}
		description={$_('admin_account.existing_voucher_help')}
	>
		<div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
			<CopyableValue
				display="({claim.id}) {claim.description}"
				class="h-9 max-w-none min-w-0 px-3 text-sm"
			/>
			<div class="flex gap-2">
				<Input
					bind:value={voucherNumber}
					placeholder={$_('admin_account.voucher_number_placeholder')}
					aria-label={$_('admin_account.voucher_number_placeholder')}
					class="md:w-48"
				/>
				<Button
					class="min-w-24"
					onclick={() => submitAccounting('number', { voucher_number: voucherNumber.trim() })}
					disabled={submitting != null ||
						isAccounted ||
						voucherNumber.trim() === '' ||
						!mayAccount(user)}
				>
					{#if submitting === 'number'}<Spinner />{:else}{$_('submit')}{/if}
				</Button>
			</div>
		</div>
	</Card>

	<Card
		title={$_(kind === 'invoice' ? 'new_invoice.form.invoice_parts.label' : 'expense_parts')}
		padded={false}
	>
		<PartsTable parts={claim.parts} owner={claim.owner} partType={kind} />
	</Card>

	<ClaimInfo {claim} linkOwner />

	<CommentsCard
		bind:comments
		currentUser={user ?? undefined}
		onSubmit={(content) => api[`${kind}s`].comment(claim.id, content)}
	/>
</ClaimDetailLayout>
