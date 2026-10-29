import { useQuery } from "@connectrpc/connect-query";
import { CircleAlert, Plus, TriangleAlert, X } from "lucide-react";
import { Amount } from "#/components/claims/badges";
import { withForm } from "#/components/form/form";
import { Button } from "#/components/ui/button";
import type { BudgetLine, CostCentre } from "#/gen/cashflow/budget/v1/budget_pb";
import { getBudget } from "#/gen/cashflow/budget/v1/budget-BudgetService_connectquery";
import type { ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { useLocale, useT } from "#/lib/i18n";
import { formatOre, parseKronor } from "#/lib/money";
import { cn } from "#/lib/utils";
import { type ClaimFormValues, emptyPart, type PartValues } from "./values";

const sameName = (a: string, b: string) => a.trim().toLowerCase() === b.trim().toLowerCase();

function findLine(budget: CostCentre[] | undefined, part: PartValues): BudgetLine | undefined {
  const cc = budget?.find((c) => sameName(c.name, part.costCentre));
  const scc = cc?.secondary.find((s) => sameName(s.name, part.secondaryCostCentre));
  return scc?.lines.find((l) => sameName(l.name, part.budgetLine));
}

/**
 * The parts of a claim: for each, cost centre → secondary cost centre →
 * budget line, narrowing step by step, and an amount. Each part shows what is
 * left on its budget line this year, counting the other parts too.
 */
export const PartsSection = withForm({
  defaultValues: {} as ClaimFormValues,
  props: { exclude: undefined as { kind: ClaimKind; number: bigint } | undefined },
  render: function PartsSection({ form, exclude }) {
    const t = useT();
    const f = t.claimForm;
    const budget = useQuery(getBudget, { exclude });
    const tree = budget.data?.costCentres;

    return (
      <div className="flex flex-col gap-4">
        {budget.isError && (
          <p className="flex items-center gap-2 rounded-lg bg-warning/15 px-3 py-2 text-sm text-warning-ink">
            <TriangleAlert className="size-4 shrink-0" /> {f.budgetUnavailable}
          </p>
        )}
        <form.AppField name="parts" mode="array">
          {(partsField) => (
            <>
              {partsField.state.value.map((_, i) => (
                // biome-ignore lint/suspicious/noArrayIndexKey: parts are addressed by index in the form
                <div key={i} className="flex flex-col gap-3 rounded-xl border p-3">
                  {partsField.state.value.length > 1 && (
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-muted-foreground text-sm">{f.part(i + 1)}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`${f.removePart} ${i + 1}`}
                        title={f.removePart}
                        onClick={() => partsField.removeValue(i)}
                      >
                        <X />
                      </Button>
                    </div>
                  )}
                  <form.Subscribe selector={(state) => state.values.parts[i]}>
                    {(part) => {
                      const cc = tree?.find((c) => sameName(c.name, part?.costCentre ?? ""));
                      const scc = cc?.secondary.find((s) => sameName(s.name, part?.secondaryCostCentre ?? ""));
                      return (
                        <div className="grid gap-3 md:grid-cols-2">
                          <form.AppField
                            name={`parts[${i}].costCentre`}
                            listeners={{
                              onChange: () => {
                                form.setFieldValue(`parts[${i}].secondaryCostCentre`, "");
                                form.setFieldValue(`parts[${i}].budgetLine`, "");
                              },
                            }}
                          >
                            {(field) => (
                              <field.ComboboxField
                                label={f.costCentre}
                                description={f.costCentreHint}
                                options={tree?.map((c) => c.name) ?? []}
                                disabledReason={budget.isPending ? f.loadingBudget : undefined}
                              />
                            )}
                          </form.AppField>
                          <form.AppField
                            name={`parts[${i}].secondaryCostCentre`}
                            listeners={{ onChange: () => form.setFieldValue(`parts[${i}].budgetLine`, "") }}
                          >
                            {(field) => (
                              <field.ComboboxField
                                label={f.secondaryCostCentre}
                                options={cc?.secondary.map((s) => s.name) ?? []}
                                disabledReason={part?.costCentre ? undefined : f.chooseCostCentreFirst}
                              />
                            )}
                          </form.AppField>
                          <form.AppField name={`parts[${i}].budgetLine`}>
                            {(field) => (
                              <field.ComboboxField
                                label={f.budgetLine}
                                options={scc?.lines.map((l) => l.name) ?? []}
                                disabledReason={part?.secondaryCostCentre ? undefined : f.chooseSecondaryFirst}
                              />
                            )}
                          </form.AppField>
                          <form.AppField name={`parts[${i}].amount`}>
                            {(field) => <field.AmountField label={f.amount} />}
                          </form.AppField>
                        </div>
                      );
                    }}
                  </form.Subscribe>
                  <form.Subscribe selector={(state) => state.values.parts}>
                    {(parts) => <BudgetHint parts={parts} index={i} tree={tree} />}
                  </form.Subscribe>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                className="self-start"
                onClick={() => partsField.pushValue({ ...emptyPart })}
              >
                <Plus /> {f.addPart}
              </Button>
            </>
          )}
        </form.AppField>

        <form.Subscribe selector={(state) => state.values.parts}>
          {(parts) => {
            const total = parts.reduce((sum, p) => sum + (parseKronor(p.amount) ?? 0n), 0n);
            return (
              <div className="flex items-center justify-between border-t pt-4 font-medium">
                <span>{f.total}</span>
                <Amount ore={total} className="text-lg" />
              </div>
            );
          }}
        </form.Subscribe>
      </div>
    );
  },
});

/**
 * How much is left on a part's budget line this year. Parts of this claim on
 * the same line count too, since they are not in the server's figure yet.
 * Going over is a warning, not a block, as in Cashflow 3.
 */
function BudgetHint({ parts, index, tree }: { parts: PartValues[]; index: number; tree: CostCentre[] | undefined }) {
  const t = useT();
  const locale = useLocale();
  const part = parts[index];
  const line = part && findLine(tree, part);
  if (!part || !line || line.expenseOre === 0n) return null;

  const onLine = parts.filter((p) => findLine(tree, p)?.id === line.id);
  // Show it once per line, under its last part.
  if (onLine.at(-1) !== part) return null;
  const thisClaim = onLine.reduce((sum, p) => sum + (parseKronor(p.amount) ?? 0n), 0n);
  const left = line.expenseOre - line.usedOre - thisClaim;
  const kr = (ore: bigint) => `${formatOre(ore, locale)} ${t.money.currency}`;

  return (
    <p
      className={cn(
        "flex items-start gap-2 text-sm",
        left < 0n ? "rounded-lg bg-warning/15 px-3 py-2 text-warning-ink" : "text-muted-foreground",
      )}
    >
      {left < 0n ? (
        <TriangleAlert className="mt-0.5 size-4 shrink-0" />
      ) : (
        <CircleAlert className="mt-0.5 size-4 shrink-0" />
      )}
      {left < 0n
        ? t.claimForm.budgetOver(kr(-left), kr(line.expenseOre))
        : t.claimForm.budgetLeft(kr(left), kr(line.expenseOre))}
    </p>
  );
}
