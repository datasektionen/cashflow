import { create, each, enforce, only, test, warn } from 'vest';
import type { VoucherRowDraft } from './VoucherRowFields.svelte';

type AccountFormData = {
	voucherRowDrafts: VoucherRowDraft[];
	expectedTotal?: number;
};

const toCents = (n: number | null | undefined) => Math.round((n ?? 0) * 100);
const sumCents = (drafts: VoucherRowDraft[], pick: (draft: VoucherRowDraft) => number | null) =>
	drafts.reduce((sum, draft) => sum + toCents(pick(draft)), 0);

export enum VoucherRowField {
	Rows = 'voucher-rows',
	Amounts = 'amounts',
	DebitCredit = 'debit-credit',
	ExpectedTotal = 'expected-total'
}

export enum ValidationError {
	VoucherRowRequired = 'voucher_row_required',
	NonPositiveAmount = 'non_positive_amount',
	DebitCreditMismatch = 'debit_credit_mismatch',
	DebitTotalMismatch = 'debit_mismatch'
}

// A field only gets a key once it has failed, hence Partial.
export type VoucherRowErrors = Partial<Record<VoucherRowField, ValidationError[]>>;
export type VoucherRowWarnings = VoucherRowErrors;

export const voucherRowValidation = create((data: AccountFormData, currentField?: string) => {
	only(currentField);

	test(VoucherRowField.Rows, ValidationError.VoucherRowRequired, () => {
		enforce(data.voucherRowDrafts).isArray().isNotEmpty();
	});

	// Assert positive amounts
	test(VoucherRowField.Amounts, ValidationError.NonPositiveAmount, () => {
		each(data.voucherRowDrafts, (draft) => {
			if (!draft.debit || draft.debit === 0) {
				enforce(draft.credit).greaterThan(0);
			} else {
				enforce(draft.debit).greaterThan(0);
			}
		});
	});

	// The total debit and credit amounts must be equal
	test(VoucherRowField.DebitCredit, ValidationError.DebitCreditMismatch, () => {
		const debitCents = sumCents(data.voucherRowDrafts, (r) => r.debit);
		const creditCents = sumCents(data.voucherRowDrafts, (r) => r.credit);

		enforce(debitCents).equals(creditCents);
	});

	// Check total debit amount against uploaded amount.
	test(VoucherRowField.ExpectedTotal, ValidationError.DebitTotalMismatch, () => {
		warn();

		if (data.expectedTotal == null) return;

		const debitCents = sumCents(data.voucherRowDrafts, (r) => r.debit);

		enforce(debitCents).equals(toCents(data.expectedTotal));
	});
});
