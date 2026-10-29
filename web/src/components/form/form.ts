import { createFormHook } from "@tanstack/react-form";
import { fieldContext, formContext } from "./context";
import { SubmitButton } from "./submit-button";
import { TextField } from "./text-field";

/**
 * The app's form hook. Fields render as `<form.AppField name="x">{(f) => <f.TextField … />}</form.AppField>`,
 * so every form gets the same labels, error display and server-error handling.
 */
export const { useAppForm, withForm } = createFormHook({
  fieldContext,
  formContext,
  fieldComponents: { TextField },
  formComponents: { SubmitButton },
});
