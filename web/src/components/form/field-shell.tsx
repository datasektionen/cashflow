import type { ReactNode } from "react";
import { Field, FieldDescription, FieldError, FieldLabel } from "#/components/ui/field";
import { cn } from "#/lib/utils";
import { useFieldContext } from "./context";

/**
 * The surrounding field's errors, once the user has left the field or tried
 * to submit, so nobody is scolded while still typing.
 */
export function useVisibleErrors() {
  const field = useFieldContext<unknown>();
  const errors = field.state.meta.errors.filter(Boolean).map((message) => ({ message: String(message) }));
  const visible = errors.length > 0 && (field.state.meta.isTouched || field.form.state.submissionAttempts > 0);
  return { field, errors: visible ? errors : [] };
}

/** Clears a server error when the value changes: it described the old value. */
export function useClearServerError() {
  const field = useFieldContext<unknown>();
  return () => field.setMeta((meta) => ({ ...meta, errorMap: { ...meta.errorMap, onServer: undefined } }));
}

/** Label, hint and errors around a form control, the same for every field type. */
export function FieldShell({
  label,
  description,
  htmlFor,
  children,
  className,
  disabled = false,
  cell = false,
}: {
  label: ReactNode;
  description?: ReactNode;
  htmlFor?: string;
  children: ReactNode;
  className?: string;
  /** A field the user can't use yet shows its hint, never an error they can't act on. */
  disabled?: boolean;
  /** In a table cell: the column header is the visible label, and errors are small. */
  cell?: boolean;
}) {
  const { field, errors } = useVisibleErrors();
  const invalid = errors.length > 0 && !disabled;
  return (
    <Field data-invalid={invalid || undefined} className={cn(cell && "gap-1", className)}>
      <FieldLabel htmlFor={htmlFor ?? field.name} className={cn(cell && "sr-only")}>
        {label}
      </FieldLabel>
      {children}
      {description && !invalid && !cell && <FieldDescription>{description}</FieldDescription>}
      {invalid && <FieldError errors={errors} className={cn(cell && "text-xs")} />}
    </Field>
  );
}
