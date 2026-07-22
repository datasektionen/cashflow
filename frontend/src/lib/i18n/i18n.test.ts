import { test, assert } from 'vitest';
import sv from './sv.json';
import en from './en.json';

/** Flatten a nested message dictionary into dotted key paths, e.g. "errors.not_found". */
function flatten(obj: Record<string, unknown>, prefix = ''): string[] {
	return Object.entries(obj).flatMap(([key, value]) => {
		const path = prefix ? `${prefix}.${key}` : key;
		return typeof value === 'object' && value !== null
			? flatten(value as Record<string, unknown>, path)
			: [path];
	});
}

test('sv and en expose identical translation keys', () => {
	const svKeys = new Set(flatten(sv));
	const enKeys = new Set(flatten(en));

	const missingInEn = [...svKeys].filter((k) => !enKeys.has(k));
	const missingInSv = [...enKeys].filter((k) => !svKeys.has(k));

	assert(
		missingInEn.length === 0,
		`keys present in sv but missing in en: ${missingInEn.join(', ')}`
	);
	assert(
		missingInSv.length === 0,
		`keys present in en but missing in sv: ${missingInSv.join(', ')}`
	);
});

test('no translation value is blank', () => {
	for (const [locale, dict] of Object.entries({ sv, en })) {
		const blanks = flatten(dict).filter((path) => {
			const value = path
				.split('.')
				.reduce<unknown>((o, k) => (o as Record<string, unknown>)[k], dict);
			return typeof value === 'string' && value.trim() === '';
		});
		assert(blanks.length === 0, `blank ${locale} translations: ${blanks.join(', ')}`);
	}
});
