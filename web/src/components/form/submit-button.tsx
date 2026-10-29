import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "#/components/ui/button";
import { useFormContext } from "./context";

/**
 * Submits the surrounding form; disabled while submitting, and with
 * requireChanges also until something has changed (edit forms).
 */
export function SubmitButton({ children, requireChanges = false }: { children: ReactNode; requireChanges?: boolean }) {
  const form = useFormContext();
  return (
    <form.Subscribe selector={(state) => [state.isSubmitting, state.isDirty] as const}>
      {([isSubmitting, isDirty]) => (
        <Button type="submit" disabled={isSubmitting || (requireChanges && !isDirty)}>
          {isSubmitting && <Loader2 className="animate-spin" />}
          {children}
        </Button>
      )}
    </form.Subscribe>
  );
}
