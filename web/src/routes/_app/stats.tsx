import { createFileRoute } from "@tanstack/react-router";
import { Page } from "#/components/layout/page";
import { ComingSoon } from "#/components/layout/states";
import { useT } from "#/lib/i18n";

export const Route = createFileRoute("/_app/stats")({
  component: StatsPage,
});

function StatsPage() {
  const t = useT();
  return (
    <Page title={t.nav.stats}>
      <ComingSoon />
    </Page>
  );
}
