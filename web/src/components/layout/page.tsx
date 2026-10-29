import type { ReactNode } from "react";

/** The standard page frame: a centred column with a title row. */
export function Page({
  eyebrow,
  title,
  actions,
  children,
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <main className="mx-auto w-full max-w-6xl p-6 md:p-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          {eyebrow && <p className="text-muted-foreground text-sm">{eyebrow}</p>}
          <h1 className="font-display font-semibold text-3xl tracking-tight md:text-4xl">{title}</h1>
        </div>
        {actions && <div className="flex gap-2">{actions}</div>}
      </div>
      <div className="mt-8">{children}</div>
    </main>
  );
}
