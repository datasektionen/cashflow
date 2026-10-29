import { useQuery } from "@connectrpc/connect-query";
import { SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";
import { useAppForm } from "#/components/form/form";
import { Button } from "#/components/ui/button";
import { FieldGroup, FieldLabel } from "#/components/ui/field";
import { Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle } from "#/components/ui/sheet";
import { ToggleGroup, ToggleGroupItem } from "#/components/ui/toggle-group";
import { getBudget } from "#/gen/cashflow/budget/v1/budget-BudgetService_connectquery";
import { formatDate } from "#/lib/claims";
import { type Messages, useLocale, useT } from "#/lib/i18n";
import { ADVANCED_KEYS, type AdvancedSearch, advancedCount, type ClaimSearch, FLAGS, type Flag } from "./claim-search";

type Values = {
  cc: string;
  scc: string;
  line: string;
  from: string;
  to: string;
  owner: string;
  inv: string;
  ver: string;
  pay: string;
} & Record<Flag, "any" | "yes" | "no">;

const toValues = (s: ClaimSearch): Values => ({
  cc: s.cc ?? "",
  scc: s.scc ?? "",
  line: s.line ?? "",
  from: s.from ?? "",
  to: s.to ?? "",
  owner: s.owner ?? "",
  inv: s.inv ?? "",
  ver: s.ver ?? "",
  pay: s.pay ? `Data${s.pay}` : "",
  ...(Object.fromEntries(FLAGS.map((flag) => [flag, s[flag] === undefined ? "any" : s[flag] ? "yes" : "no"])) as Record<
    Flag,
    "any" | "yes" | "no"
  >),
});

const blank = (text: string) => text.trim() || undefined;

function toSearch(v: Values): Partial<ClaimSearch> {
  const pay = Number.parseInt(v.pay.replace(/\D/g, ""), 10);
  return {
    cc: blank(v.cc),
    scc: blank(v.scc),
    line: blank(v.line),
    from: blank(v.from),
    to: blank(v.to),
    owner: blank(v.owner),
    inv: blank(v.inv),
    ver: blank(v.ver)?.toUpperCase(),
    pay: pay > 0 ? pay : undefined,
    ...Object.fromEntries(FLAGS.map((flag) => [flag, v[flag] === "any" ? undefined : v[flag] === "yes"])),
  };
}

const cleared: Partial<ClaimSearch> = Object.fromEntries(["cc", ...ADVANCED_KEYS].map((key) => [key, undefined]));

/**
 * Every other way to narrow a claims list, in a side panel: budget names
 * narrowing step by step, dates, people, numbers and status. Nothing applies
 * until "Visa", so half-filled fields never flash an empty list.
 */
export function FilterPanel({
  search,
  onSearch,
  hide = [],
}: {
  search: ClaimSearch;
  onSearch: (change: Partial<ClaimSearch>) => void;
  /** Filters the list already fixes, e.g. "accounted" on the vouchers page. */
  hide?: Flag[];
}) {
  const t = useT();
  const f = t.filters;
  const [open, setOpen] = useState(false);
  const budget = useQuery(getBudget, {}, { enabled: open, staleTime: 10 * 60 * 1000 });
  const form = useAppForm({
    defaultValues: toValues(search),
    onSubmit: ({ value }) => {
      onSearch(toSearch(value));
      setOpen(false);
    },
  });

  const tree = budget.data?.costCentres ?? [];
  const same = (a: string, b: string) => a.trim().toLowerCase() === b.trim().toLowerCase();

  return (
    <Sheet
      open={open}
      onOpenChange={(next) => {
        // Opening starts from what the list shows now.
        if (next) form.reset(toValues(search));
        setOpen(next);
      }}
    >
      <Button variant="outline" onClick={() => setOpen(true)}>
        <SlidersHorizontal /> {f.button}
        {advancedCount(search) > 0 && (
          <span className="rounded-full bg-primary px-1.5 font-medium text-primary-foreground text-xs">
            {advancedCount(search)}
          </span>
        )}
      </Button>
      <SheetContent className="gap-0 overflow-y-auto">
        <form
          noValidate
          className="flex flex-1 flex-col"
          onSubmit={(event) => {
            event.preventDefault();
            void form.handleSubmit();
          }}
        >
          <SheetHeader>
            <SheetTitle>{f.title}</SheetTitle>
            <SheetDescription className="sr-only">{f.title}</SheetDescription>
          </SheetHeader>
          <FieldGroup className="gap-3 px-4 pb-4">
            <form.Subscribe selector={(state) => [state.values.cc, state.values.scc] as const}>
              {([cc, scc]) => {
                const ccNode = tree.find((c) => same(c.name, cc));
                const sccNode = ccNode?.secondary.find((s) => same(s.name, scc));
                return (
                  <>
                    <form.AppField
                      name="cc"
                      listeners={{
                        onChange: () => {
                          form.setFieldValue("scc", "");
                          form.setFieldValue("line", "");
                        },
                      }}
                    >
                      {(field) => (
                        <field.ComboboxField
                          clearable
                          label={t.claimForm.costCentre}
                          options={tree.map((c) => c.name)}
                          placeholder={f.any}
                        />
                      )}
                    </form.AppField>
                    <form.AppField name="scc" listeners={{ onChange: () => form.setFieldValue("line", "") }}>
                      {(field) => (
                        <field.ComboboxField
                          clearable
                          label={f.secondaryCostCentre}
                          options={ccNode?.secondary.map((s) => s.name) ?? []}
                          placeholder={f.any}
                          disabledReason={ccNode ? undefined : t.claimForm.chooseCostCentreFirst}
                        />
                      )}
                    </form.AppField>
                    <form.AppField name="line">
                      {(field) => (
                        <field.ComboboxField
                          clearable
                          label={f.budgetLine}
                          options={sccNode?.lines.map((l) => l.name) ?? []}
                          placeholder={f.any}
                          disabledReason={sccNode ? undefined : t.claimForm.chooseSecondaryFirst}
                        />
                      )}
                    </form.AppField>
                  </>
                );
              }}
            </form.Subscribe>
            <div className="grid grid-cols-2 gap-3">
              <form.AppField name="from">{(field) => <field.TextField type="date" label={f.from} />}</form.AppField>
              <form.AppField name="to">{(field) => <field.TextField type="date" label={f.to} />}</form.AppField>
            </div>
            <form.AppField name="owner">
              {(field) => <field.TextField label={f.owner} autoComplete="off" />}
            </form.AppField>
            <div className="grid grid-cols-3 gap-3">
              <form.AppField name="inv">
                {(field) => <field.TextField label={f.invoiceNumber} autoComplete="off" />}
              </form.AppField>
              <form.AppField name="ver">
                {(field) => <field.TextField label={f.verification} placeholder="E12" autoComplete="off" />}
              </form.AppField>
              <form.AppField name="pay">
                {(field) => (
                  <field.TextField label={f.payment} placeholder="Data12" title={f.paymentHint} autoComplete="off" />
                )}
              </form.AppField>
            </div>
            <fieldset className="flex flex-col gap-2">
              <legend className="mb-1 font-medium text-sm">{f.status}</legend>
              {FLAGS.filter((flag) => !hide.includes(flag)).map((flag) => (
                <form.Field key={flag} name={flag}>
                  {(field) => (
                    <div className="flex items-center justify-between gap-3">
                      <FieldLabel className="font-normal">{f.flags[flag]}</FieldLabel>
                      <ToggleGroup
                        variant="outline"
                        size="sm"
                        aria-label={f.flags[flag]}
                        value={[field.state.value]}
                        onValueChange={(value: string[]) => {
                          const next = value[0];
                          if (next) field.handleChange(next as Values[Flag]);
                        }}
                      >
                        {(["any", "yes", "no"] as const).map((v) => (
                          <ToggleGroupItem key={v} value={v} className="px-2.5">
                            {f[v]}
                          </ToggleGroupItem>
                        ))}
                      </ToggleGroup>
                    </div>
                  )}
                </form.Field>
              ))}
            </fieldset>
          </FieldGroup>
          <SheetFooter className="mt-auto flex-row justify-between border-t">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                onSearch(cleared);
                setOpen(false);
              }}
            >
              {f.clear}
            </Button>
            <Button type="submit">{f.done}</Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}

/** The panel's filters as removable chips, so it is always clear what narrows the list. */
export function FilterChips({
  search,
  onSearch,
}: {
  search: ClaimSearch;
  onSearch: (change: Partial<ClaimSearch>) => void;
}) {
  const t = useT();
  const locale = useLocale();
  const chips = describeFilters(search, t, locale);
  return chips.map(({ key, label }) => (
    <Button key={key} variant="secondary" size="sm" className="gap-1.5" onClick={() => onSearch({ [key]: undefined })}>
      {label}
      <X />
    </Button>
  ));
}

function describeFilters(s: AdvancedSearch, t: Messages, locale: ReturnType<typeof useLocale>) {
  const f = t.filters;
  const chips: Array<{ key: keyof AdvancedSearch; label: string }> = [];
  const add = (key: keyof AdvancedSearch, name: string, value: string | undefined) => {
    if (value) chips.push({ key, label: `${name}: ${value}` });
  };
  add("scc", f.secondaryCostCentre, s.scc);
  add("line", f.budgetLine, s.line);
  add("from", f.from, s.from && formatDate(s.from, locale));
  add("to", f.to, s.to && formatDate(s.to, locale));
  add("owner", t.claims.columns.owner, s.owner);
  add("inv", f.invoiceNumber, s.inv);
  add("ver", f.verification, s.ver);
  add("pay", f.payment, s.pay ? `Data${s.pay}` : undefined);
  for (const flag of FLAGS) {
    if (s[flag] !== undefined) chips.push({ key: flag, label: `${f.flags[flag]}: ${s[flag] ? f.yes : f.no}` });
  }
  return chips;
}
