import { enforce, include, test, warn } from 'vest';
import { add, greaterThan, type Dinero } from 'dinero.js';
import type { PartCreateUpdate } from '$lib/api/types';
import { sumDinero } from '$lib/money';

/**
 * How much of a budget line's expense budget is used, not counting the
 * claim being edited.
 */
export type BudgetLineUsage = {
	budget: Dinero<number, 'SEK'>;
	// Uploaded amount on the budget line, excluding the parts the claim was
	// saved with (those are replaced by the parts in the form).
	uploaded: Dinero<number, 'SEK'>;
};

/**
 * A field without tests of its own. Running a suite for it only re-runs the
 * budget line warnings, e.g. after an amount or a budget line's usage changed.
 */
export const BUDGET_USAGE_FIELD = 'budget-usage';

export function sameBudgetLine(a: PartCreateUpdate, b: PartCreateUpdate): boolean {
	return (
		a.cost_centre === b.cost_centre &&
		a.secondary_cost_centre === b.secondary_cost_centre &&
		a.budget_line === b.budget_line
	);
}

/**
 * Warns if saving the parts would make the budget line of part `i` exceed its budget.
 *
 * The test runs whenever the budget line's usage is known, so that changing
 * any amount in the form updates the warning.
 */
export function testBudgetLineExceeded(
	parts: PartCreateUpdate[],
	budgetUsage: (BudgetLineUsage | null)[],
	i: number
) {
	const usage = budgetUsage[i];
	const field = `part-${i}-budgetline`;
	include(field).when(usage != null);

	test(field, 'budget_line_exceeded', () => {
		warn();
		if (usage == null) return;

		const onLine = sumDinero(parts.filter((p) => sameBudgetLine(p, parts[i])).map((p) => p.amount));
		enforce(greaterThan(add(usage.uploaded, onLine), usage.budget)).isFalsy();
	});
}
