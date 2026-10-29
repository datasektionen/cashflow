import type { ComponentProps, ReactNode } from "react";
import { Input } from "#/components/ui/input";
import { useFieldContext } from "./context";
import { FieldShell, useClearServerError, useVisibleErrors } from "./field-shell";

type Props = Omit<ComponentProps<typeof Input>, "id" | "name" | "value" | "onChange" | "onBlur"> & {
  label: ReactNode;
  description?: ReactNode;
};

/** A labelled text input bound to the surrounding form field. */
export function TextField({ label, description, className, ...inputProps }: Props) {
  const field = useFieldContext<string>();
  const { errors } = useVisibleErrors();
  const clearServerError = useClearServerError();
  return (
    <FieldShell label={label} description={description}>
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
