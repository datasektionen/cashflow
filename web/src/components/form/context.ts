import { createFormHookContexts } from "@tanstack/react-form";

// Split from form.ts so field components can read the contexts without a cycle.
export const { fieldContext, formContext, useFieldContext, useFormContext } = createFormHookContexts();
