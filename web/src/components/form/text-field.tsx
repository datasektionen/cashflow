import type { ComponentProps } from "react";
import { Field, FieldDescription, FieldError, FieldLabel } from "#/components/ui/field";
import { Input } from "#/components/ui/input";
import { useFieldContext } from "./context";

type Props = Omit<ComponentProps<typeof Input>, "id" | "name" | "value" | "onChange" | "onBlur"> & {
  label: string;
  description?: string;
};

/** A labelled text input bound to the surrounding form field. */
export function TextField({ label, description, ...inputProps }: Props) {
  const field = useFieldContext<string>();
  const errors = field.state.meta.errors.filter(Boolean).map((message) => ({ message: String(message) }));
  // Show errors once the user has left the field or tried to submit.
  const showErrors = errors.length > 0 && (field.state.meta.isTouched || field.form.state.submissionAttempts > 0);

  return (
    <Field data-invalid={showErrors || undefined}>
      <FieldLabel htmlFor={field.name}>{label}</FieldLabel>
      <Input
        id={field.name}
        name={field.name}
        value={field.state.value}
        aria-invalid={showErrors || undefined}
        onBlur={field.handleBlur}
        onChange={(event) => {
          // A server error describes the value that was sent; editing clears it.
          field.setMeta((meta) => ({ ...meta, errorMap: { ...meta.errorMap, onServer: undefined } }));
          field.handleChange(event.target.value);
        }}
        {...inputProps}
      />
      {description && !showErrors && <FieldDescription>{description}</FieldDescription>}
      {showErrors && <FieldError errors={errors} />}
    </Field>
  );
}
