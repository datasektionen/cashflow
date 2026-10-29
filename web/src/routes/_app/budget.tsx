import { createFileRoute } from "@tanstack/react-router";
import { BudgetPage, type BudgetSearch } from "#/components/budget/budget-page";
import { Page } from "#/components/layout/page";
import { useT } from "#/lib/i18n";

// GOrdian numbers cost centres from 0.
const naturalInt = (min: number) => (value: unknown) =>
  typeof value === "number" && Number.isInteger(value) && value >= min ? value : undefined;

export const Route = createFileRoute("/_app/budget")({
  validateSearch: (raw: Record<string, unknown>): BudgetSearch => ({
    cc: naturalInt(0)(raw.cc),
    year: naturalInt(2000)(raw.year),
    blown: raw.blown === true ? true : undefined,
  }),
  component: Budget,
});

function Budget() {
  const t = useT();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  return (
    <Page title={t.budget.title}>
      <BudgetPage
        search={search}
        onSearch={(change) => navigate({ search: (prev) => ({ ...prev, ...change }), replace: true })}
      />
    </Page>
  );
}
