import { Loader2 } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";
import { Button } from "#/components/ui/button";
import { useFormContext } from "./context";

/**
 * Submits the surrounding form; disabled while submitting, and with
 * requireChanges also until something has changed (edit forms).
 */
export function SubmitButton({
  children,
  requireChanges = false,
  variant,
}: {
  children: ReactNode;
  requireChanges?: boolean;
  variant?: ComponentProps<typeof Button>["variant"];
}) {
  const form = useFormContext();
  return (
    <form.Subscribe selector={(state) => [state.isSubmitting, state.isDirty] as const}>
      {([isSubmitting, isDirty]) => (
        <Button type="submit" variant={variant} disabled={isSubmitting || (requireChanges && !isDirty)}>
          {isSubmitting && <Loader2 className="animate-spin" />}
          {children}
        </Button>
      )}
    </form.Subscribe>
  );
}
