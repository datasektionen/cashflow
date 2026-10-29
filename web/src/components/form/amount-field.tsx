import type { ReactNode } from "react";
import { InputGroup, InputGroupAddon, InputGroupInput, InputGroupText } from "#/components/ui/input-group";
import { useT } from "#/lib/i18n";
import { useFieldContext } from "./context";
import { FieldShell, useClearServerError, useVisibleErrors } from "./field-shell";

/**
 * An amount in kronor, typed freely ("1 234,50", "99"). The field holds the
 * text; forms turn it into öre with parseKronor when submitting.
 */
export function AmountField({
  label,
  description,
  cell = false,
  placeholder = "0,00",
}: {
  label: ReactNode;
  description?: ReactNode;
  cell?: boolean;
  placeholder?: string;
}) {
  const t = useT();
  const field = useFieldContext<string>();
  const { errors } = useVisibleErrors();
  const clearServerError = useClearServerError();
  return (
    <FieldShell label={label} description={description} cell={cell}>
      <InputGroup>
        <InputGroupInput
          id={field.name}
          name={field.name}
          inputMode="decimal"
          autoComplete="off"
          placeholder={placeholder}
          className="amount text-right"
          value={field.state.value}
          aria-invalid={errors.length > 0 || undefined}
          onBlur={field.handleBlur}
          onChange={(event) => {
            clearServerError();
            field.handleChange(event.target.value);
          }}
        />
        {!cell && (
          <InputGroupAddon align="inline-end">
            <InputGroupText>{t.money.currency}</InputGroupText>
          </InputGroupAddon>
        )}
      </InputGroup>
    </FieldShell>
  );
}
