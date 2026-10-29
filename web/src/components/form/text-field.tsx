import type { ComponentProps, ReactNode } from "react";
import { Input } from "#/components/ui/input";
import { useFieldContext } from "./context";
import { FieldShell, useClearServerError, useVisibleErrors } from "./field-shell";

type Props = Omit<ComponentProps<typeof Input>, "id" | "name" | "value" | "onChange" | "onBlur"> & {
  label: ReactNode;
  description?: ReactNode;
  /** Label for screen readers only, for compact inline forms. */
  cell?: boolean;
};

/** A labelled text input bound to the surrounding form field. */
export function TextField({ label, description, className, cell, ...inputProps }: Props) {
  const field = useFieldContext<string>();
  const { errors } = useVisibleErrors();
  const clearServerError = useClearServerError();
  return (
    <FieldShell label={label} description={description} cell={cell}>
      <Input
        id={field.name}
        name={field.name}
        value={field.state.value}
        aria-invalid={errors.length > 0 || undefined}
        onBlur={field.handleBlur}
        onChange={(event) => {
          clearServerError();
          field.handleChange(event.target.value);
        }}
        className={className}
        {...inputProps}
      />
    </FieldShell>
  );
}
