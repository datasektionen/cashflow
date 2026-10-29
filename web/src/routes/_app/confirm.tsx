import { createFileRoute } from "@tanstack/react-router";
import { Page } from "#/components/layout/page";
import { ComingSoon } from "#/components/layout/states";
import { useT } from "#/lib/i18n";

export const Route = createFileRoute("/_app/confirm")({
  component: ConfirmPage,
});

function ConfirmPage() {
  const t = useT();
  return (
    <Page title={t.nav.confirm}>
      <ComingSoon />
    </Page>
  );
}
