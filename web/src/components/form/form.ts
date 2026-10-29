import { createFormHook } from "@tanstack/react-form";
import { AmountField } from "./amount-field";
import { ComboboxField } from "./combobox-field";
import { fieldContext, formContext } from "./context";
import { FilesField } from "./files-field";
import { SubmitButton } from "./submit-button";
import { TextField } from "./text-field";

/**
 * The app's form hook. Fields render as `<form.AppField name="x">{(f) => <f.TextField … />}</form.AppField>`,
 * so every form gets the same labels, error display and server-error handling.
 */
export const { useAppForm, withForm } = createFormHook({
  fieldContext,
  formContext,
  fieldComponents: { TextField, AmountField, ComboboxField, FilesField },
  formComponents: { SubmitButton },
});
