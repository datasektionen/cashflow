import type { ReactNode } from "react";

/** The standard page frame: a centred column with a title row. */
export function Page({ title, actions, children }: { title: ReactNode; actions?: ReactNode; children: ReactNode }) {
  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-5 md:px-8 md:py-6">
      <div className="flex min-h-9 flex-wrap items-center justify-between gap-3">
        <h1 className="font-display font-semibold text-2xl tracking-tight">{title}</h1>
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>
      <div className="mt-4">{children}</div>
    </main>
  );
}
