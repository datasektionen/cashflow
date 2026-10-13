import { create, each, enforce, only, test, warn } from 'vest';
import { equal, greaterThan, isZero, type Dinero } from 'dinero.js';
import { sumDinero, ZERO } from '$lib/money';

export type VoucherRowDraft = {
	// Account number as a string (the AdvancedCombobox value), e.g. "1234".
	account: string;
	// Fortnox cost centre code, e.g. "123".
	cost_centre: string;
	description: string;
	debit: Dinero<number, 'SEK'>;
	credit: Dinero<number, 'SEK'>;
	lockedFields?: ('account' | 'cost_centre' | 'debit' | 'credit')[];
	deletable?: boolean;
};

export type AccountFormData = {
	voucherRowDrafts: VoucherRowDraft[];
	expectedTotal?: Dinero<number, 'SEK'>;
};

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
			if (isZero(draft.debit)) {
				enforce(greaterThan(draft.credit, ZERO)).isTrue();
			} else {
				enforce(greaterThan(draft.debit, ZERO)).isTrue();
			}
		});
	});

	// The total debit and credit amounts must be equal
	test(VoucherRowField.DebitCredit, ValidationError.DebitCreditMismatch, () => {
		const debitSum = sumDinero(data.voucherRowDrafts.map((r) => r.debit));
		const creditSum = sumDinero(data.voucherRowDrafts.map((r) => r.credit));

		enforce(equal(debitSum, creditSum)).isTrue();
	});

	// Check total debit amount against uploaded amount.
	test(VoucherRowField.ExpectedTotal, ValidationError.DebitTotalMismatch, () => {
		warn();

		if (data.expectedTotal == null) return;

		const totalDebit = sumDinero(data.voucherRowDrafts.map((r) => r.debit));

		enforce(equal(totalDebit, data.expectedTotal)).isTrue();
	});
});
