import { test, assert } from 'vitest';
import { formatBankAccount } from './bankAccount';

test('joins clearing and account with a dash', () => {
	assert.equal(formatBankAccount('8327', '1234567'), '8327-1234567');
});

test('deduplicates a clearing number included in the account', () => {
	assert.equal(formatBankAccount('8327', '83271234567'), '8327-1234567');
});

test('keeps an account that merely starts with the clearing digits', () => {
	assert.equal(formatBankAccount('8327', '8327123'), '8327-8327123');
});

test('strips spaces, dashes and dots before formatting', () => {
	assert.equal(formatBankAccount('8327-9', '123 456 789-0'), '83279-1234567890');
});

test('formats a valid IBAN in groups of four', () => {
	assert.equal(formatBankAccount('', 'SE4550000000058398257466'), 'SE45 5000 0000 0583 9825 7466');
});

test('returns just the account when there is no clearing number', () => {
	assert.equal(formatBankAccount('', '1234567'), '1234567');
});

test('returns just the clearing number when there is no account', () => {
	assert.equal(formatBankAccount('8327', ''), '8327');
});
