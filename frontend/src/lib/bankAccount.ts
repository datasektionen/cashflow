import { friendlyFormatIBAN, validateIBAN } from 'ibantools';

/**
 * Formats a bank account for display as `CLEARING-ACCOUNT`, tolerating account
 * numbers that already include the clearing number. Full IBANs are formatted
 * in the standard groups of four instead.
 */
export function formatBankAccount(sortingNumber: string, bankAccount: string): string {
	const clearing = sortingNumber.replace(/[\s.-]/g, '');
	const account = bankAccount.replace(/[\s.-]/g, '');

	const iban = account.toUpperCase();
	if (validateIBAN(iban).valid) {
		return friendlyFormatIBAN(iban) ?? iban;
	}

	if (!clearing) return account;
	if (!account) return clearing;

	// Swedish account numbers are at least 6 digits after the clearing number,
	// so a shorter remainder means the matching prefix belongs to the account itself.
	const rest =
		account.startsWith(clearing) && account.length - clearing.length >= 6
			? account.slice(clearing.length)
			: account;
	return `${clearing}-${rest}`;
}
