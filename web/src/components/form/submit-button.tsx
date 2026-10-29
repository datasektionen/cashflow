import { Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "#/components/ui/button";
import { useFormContext } from "./context";

/** Submits the surrounding form; disabled while submitting or unchanged. */
export function SubmitButton({ children }: { children: ReactNode }) {
  const form = useFormContext();
  return (
    <form.Subscribe selector={(state) => [state.isSubmitting, state.isDirty] as const}>
      {([isSubmitting, isDirty]) => (
        <Button type="submit" disabled={isSubmitting || !isDirty}>
          {isSubmitting && <Loader2 className="animate-spin" />}
          {children}
        </Button>
      )}
    </form.Subscribe>
  );
}
