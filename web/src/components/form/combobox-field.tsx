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
};

/**
 * Pick one of a list by typing to search. A current value that is no longer
 * among the options (an old budget name) stays visible, marked as such.
 */
export function ComboboxField({ label, description, options, disabledReason }: Props) {
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
      description={stale ? `${value}: ${t.claimForm.notInBudget}` : (disabledReason ?? description)}
      disabled={Boolean(disabledReason)}
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
          placeholder={t.claimForm.choose}
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
