import { ConnectError } from "@connectrpc/connect";
import type { AnyFormApi } from "@tanstack/react-form";
import { FieldViolationsSchema } from "#/gen/cashflow/common/v1/errors_pb";
import type { Messages } from "#/lib/i18n";

const camelCase = (field: string) => field.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());

/**
 * Shows a server's field violations next to their fields. Request fields map
 * to form fields by name (`clearing_number` → `clearingNumber`). Returns false
 * when the error carried no violations, so the caller can show a general error.
 */
export function applyServerErrors(
  form: AnyFormApi,
  error: unknown,
  t: Messages,
  /** For forms whose field names differ from the request's beyond casing. */
  rename: (field: string) => string = (field) => field,
): boolean {
  const violations = ConnectError.from(error)
    .findDetails(FieldViolationsSchema)
    .flatMap((d) => d.violations);
  for (const { field, code } of violations) {
    const message = t.validation[code] ?? t.validation.unknown;
    form.setFieldMeta(rename(camelCase(field)), (meta) => ({
      ...meta,
      errorMap: { ...meta.errorMap, onServer: message },
    }));
  }
  return violations.length > 0;
}
