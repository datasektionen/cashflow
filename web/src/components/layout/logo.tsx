import { cn } from "#/lib/utils";

/** Datasektionen's delta in cerise, next to the Cashflow wordmark. */
export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2", className)}>
      <svg viewBox="0 0 24 24" aria-hidden="true" className="size-6 shrink-0 text-cerise">
        <path d="M12 2.5 22.5 21h-21z" fill="currentColor" />
        <path d="M12 9.2 16.6 17.4H7.4z" className="fill-sidebar" />
      </svg>
      <span className="font-display text-lg font-semibold tracking-tight">
        cash<span className="text-sidebar-primary">flow</span>
      </span>
    </span>
  );
}
