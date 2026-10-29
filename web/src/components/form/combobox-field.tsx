import type { ReactNode } from "react";
import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "#/components/ui/combobox";
import { useT } from "#/lib/i18n";
import { useFieldContext } from "./context";
import { FieldShell, useClearServerError, useVisibleErrors } from "./field-shell";

type Props = {
  label: ReactNode;
  description?: ReactNode;
  options: string[];
  /** Shown instead of options while a parent choice is missing. */
  disabledReason?: string;
  cell?: boolean;
  placeholder?: string;
  /** Offers clearing the choice, for optional fields. */
  clearable?: boolean;
};

/**
 * Pick one of a list by typing to search. A current value that is no longer
 * among the options (an old budget name) stays visible, marked as such.
 */
export function ComboboxField({ label, description, options, disabledReason, cell, placeholder, clearable }: Props) {
  const t = useT();
  const field = useFieldContext<string>();
  const { errors } = useVisibleErrors();
  const clearServerError = useClearServerError();
  const value = field.state.value;
  const items = value && !options.includes(value) ? [value, ...options] : options;
  const stale = Boolean(value && !options.includes(value) && options.length > 0);

  return (
    <FieldShell
      label={label}
      description={stale ? `${value}: ${t.claimForm.notInBudget}` : description}
      disabled={Boolean(disabledReason)}
      cell={cell}
    >
      <Combobox
        items={items}
        value={value || null}
        disabled={Boolean(disabledReason)}
        onValueChange={(next: string | null) => {
          clearServerError();
          field.handleChange(next ?? "");
        }}
      >
        <ComboboxInput
          id={field.name}
          // Why it can't be used yet, where the user is looking.
          placeholder={disabledReason ?? placeholder ?? t.claimForm.choose}
          showClear={clearable && Boolean(value)}
          aria-invalid={(errors.length > 0 && !disabledReason) || undefined}
          onBlur={field.handleBlur}
          disabled={Boolean(disabledReason)}
        />
        <ComboboxContent>
          <ComboboxEmpty>{t.claimForm.noMatches}</ComboboxEmpty>
          <ComboboxList>
            {(item: string) => (
              <ComboboxItem key={item} value={item}>
                {item}
              </ComboboxItem>
            )}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
    </FieldShell>
  );
}
