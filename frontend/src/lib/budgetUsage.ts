import { enforce, include, test, warn } from 'vest';
import {
	add,
	dinero,
	greaterThan,
	isNegative,
	isZero,
	lessThan,
	subtract,
	type Dinero
} from 'dinero.js';
import { SEK } from 'dinero.js/currencies';
import type { PartCreateUpdate } from '#lib/api/types.ts';
import { sumDinero } from '#lib/money.ts';

/** A budget line's expense budget and usage, not counting the claim being edited. */
export type BudgetLineUsage = {
	budget: Dinero<number, 'SEK'>;
	uploaded: Dinero<number, 'SEK'>;
};

/** A field without tests of its own; validating it only re-runs the budget line warnings. */
export const BUDGET_USAGE_FIELD = 'budget-usage';

export function sameBudgetLine(a: PartCreateUpdate, b: PartCreateUpdate): boolean {
	return (
		a.cost_centre === b.cost_centre &&
		a.secondary_cost_centre === b.secondary_cost_centre &&
		a.budget_line === b.budget_line
	);
}

/** What is left on the budget line of part `i` after saving the parts; negative when exceeded. */
export function budgetLineRemaining(
	parts: PartCreateUpdate[],
	budgetUsage: (BudgetLineUsage | null)[],
	i: number
): Dinero<number, 'SEK'> | null {
	const usage = budgetUsage[i];
	if (usage == null) return null;
	const onLine = sumDinero(parts.filter((p) => sameBudgetLine(p, parts[i])).map((p) => p.amount));
	return subtract(usage.budget, add(usage.uploaded, onLine));
}

/** Warns if saving the parts would exceed the budget line of part `i`. */
function testBudgetLineExceeded(
	parts: PartCreateUpdate[],
	budgetUsage: (BudgetLineUsage | null)[],
	i: number
) {
	const usage = budgetUsage[i];
	const field = `part-${i}-budgetline`;
	include(field).when(usage != null);

	test(field, 'budget_line_exceeded', () => {
		warn();
		const remaining = budgetLineRemaining(parts, budgetUsage, i);
		if (remaining) enforce(isNegative(remaining)).isFalsy();
	});
}

/** The tests every claim form runs for its parts. */
export function testParts(parts: PartCreateUpdate[], budgetUsage: (BudgetLineUsage | null)[]) {
	parts?.forEach((part, i) => {
		testBudgetLineExceeded(parts, budgetUsage, i);
		test(`part-${i}-costcenter`, 'cost_center_required', () => {
			enforce(part.cost_centre).isNotBlank();
		});
		test(`part-${i}-secondarycostcenter`, 'secondary_cost_center_required', () => {
			enforce(part.secondary_cost_centre).isNotBlank();
		});
		test(`part-${i}-budgetline`, 'budget_line_required', () => {
			enforce(part.budget_line).isNotBlank();
		});
		test(`part-${i}-amount`, 'amount_required', () => {
			enforce(isZero(part.amount)).isFalsy();
		});
		test(`part-${i}-amount`, 'amount_negative', () => {
			const zero = dinero({ amount: 0, currency: SEK });
			enforce(greaterThan(part.amount, zero)).isTruthy();
		});
		test(`part-${i}-amount`, 'amount_too_large', () => {
			const maxAmount = dinero({ amount: 999999999, currency: SEK });
			enforce(lessThan(part.amount, maxAmount)).isTruthy();
		});
	});
}
