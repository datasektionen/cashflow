import { useSuspenseQuery } from "@connectrpc/connect-query";
import { createFileRoute } from "@tanstack/react-router";
import { FileText, Receipt } from "lucide-react";
import { Page } from "#/components/layout/page";
import { StateCard } from "#/components/layout/states";
import { ButtonLink } from "#/components/ui/button-link";
import { Card, CardDescription, CardHeader, CardTitle } from "#/components/ui/card";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { useLocale, useT } from "#/lib/i18n";
import { formatOre } from "#/lib/money";

export const Route = createFileRoute("/_app/")({
  component: Overview,
});

function Overview() {
  const t = useT();
  const { data } = useSuspenseQuery(getMe, {});
  const firstName = data.user?.name.split(" ")[0] ?? "";

  return (
    <Page
      eyebrow={t.overview.greeting(firstName)}
      title={t.overview.title}
      actions={
        <>
          <ButtonLink variant="outline" to="/invoices/new">
            <FileText /> {t.nav.newInvoice}
          </ButtonLink>
          <ButtonLink to="/expenses/new">
            <Receipt /> {t.nav.newExpense}
          </ButtonLink>
        </>
      }
    >
      {/* Totals come from the claims service in phase 1. */}
      <div className="grid gap-4 md:grid-cols-3">
        <Total label={t.overview.awaitingAttest} ore={0n} />
        <Total label={t.overview.awaitingPayment} ore={0n} />
        <Total label={t.overview.paidThisYear} ore={0n} />
      </div>

      <StateCard
        className="mt-8"
        icon={<Receipt />}
        title={t.overview.emptyTitle}
        description={t.overview.emptyBody}
        action={<ButtonLink to="/expenses/new">{t.overview.emptyAction}</ButtonLink>}
      />
    </Page>
  );
}

function Total({ label, ore }: { label: string; ore: bigint }) {
  const t = useT();
  const locale = useLocale();
  return (
    <Card className="receipt-edge rounded-b-none">
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="amount font-medium text-2xl">
          {formatOre(ore, locale)} <span className="font-sans text-muted-foreground text-sm">{t.money.currency}</span>
        </CardTitle>
      </CardHeader>
    </Card>
  );
}
