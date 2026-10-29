import { Construction } from "lucide-react";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "#/components/ui/empty";

/** Placeholder for pages that are not ported from Cashflow 3 yet. */
export function ComingSoon({ title }: { title: string }) {
  return (
    <main className="mx-auto w-full max-w-6xl p-6 md:p-10">
      <h1 className="font-display text-3xl font-semibold tracking-tight">{title}</h1>
      <Empty className="ledger mt-8 rounded-xl border border-dashed bg-card">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Construction />
          </EmptyMedia>
          <EmptyTitle>Inte klart än</EmptyTitle>
          <EmptyDescription>Den här sidan flyttas över från Cashflow 3 i en senare fas.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    </main>
  );
}
