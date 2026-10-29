import { createFileRoute } from "@tanstack/react-router";
import { ComingSoon } from "#/components/layout/coming-soon";

export const Route = createFileRoute("/_app/payments")({
  component: () => <ComingSoon title="Utbetalningar" />,
});
