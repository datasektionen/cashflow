import { useSuspenseQuery } from "@connectrpc/connect-query";
import { createFileRoute } from "@tanstack/react-router";
import { FileText, Receipt } from "lucide-react";
import { ButtonLink } from "#/components/ui/button-link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "#/components/ui/card";
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "#/components/ui/empty";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";

export const Route = createFileRoute("/_app/")({
  component: Overview,
});

function Overview() {
  const { data } = useSuspenseQuery(getMe, {});
  const firstName = data.user?.name.split(" ")[0] ?? "";

  return (
    <main className="mx-auto w-full max-w-6xl p-6 md:p-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Hej {firstName}</p>
          <h1 className="font-display text-3xl font-semibold tracking-tight md:text-4xl">Dina utlägg</h1>
        </div>
        <div className="flex gap-2">
          <ButtonLink variant="outline" to="/invoices/new">
            <FileText /> Ny faktura
          </ButtonLink>
          <ButtonLink to="/expenses/new">
            <Receipt /> Nytt utlägg
          </ButtonLink>
        </div>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <Stat label="Väntar på attest" value="0,00" />
        <Stat label="Väntar på utbetalning" value="0,00" />
        <Stat label="Utbetalt i år" value="0,00" />
      </div>

      <Empty className="ledger mt-8 rounded-xl border border-dashed bg-card text-muted-foreground">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <Receipt />
          </EmptyMedia>
          <EmptyTitle className="text-foreground">Inga utlägg än</EmptyTitle>
          <EmptyDescription>
            Ladda upp ett kvitto så sköter attestanter och kassör resten. Du ser varje steg här.
          </EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <ButtonLink to="/expenses/new">Lägg till ett utlägg</ButtonLink>
        </EmptyContent>
      </Empty>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <Card className="receipt-edge gap-1 rounded-b-none">
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="amount text-2xl font-medium">
          {value} <span className="font-sans text-sm text-muted-foreground">kr</span>
        </CardTitle>
      </CardHeader>
      <CardContent />
    </Card>
  );
}
