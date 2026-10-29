import { timestampDate } from "@bufbuild/protobuf/wkt";
import { createConnectQueryKey, useMutation, useQuery, useTransport } from "@connectrpc/connect-query";
import { useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { CircleCheckBig, Landmark, Loader2, PlugZap, Power, ScrollText } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { problemMessage } from "#/components/claim/use-claim-action";
import { Page } from "#/components/layout/page";
import { StateCard } from "#/components/layout/states";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "#/components/ui/alert-dialog";
import { Button, buttonVariants } from "#/components/ui/button";
import { ButtonLink } from "#/components/ui/button-link";
import { Card, CardContent } from "#/components/ui/card";
import { Skeleton } from "#/components/ui/skeleton";
import {
  disconnectFortnox,
  getFortnoxStatus,
} from "#/gen/cashflow/accounting/v1/accounting-AccountingService_connectquery";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { intlLocale, useLocale, useT } from "#/lib/i18n";

const RESULTS = ["connected", "cancelled", "error", "forbidden", "disabled"] as const;
type Result = (typeof RESULTS)[number];

export const Route = createFileRoute("/_app/fortnox")({
  // The server's OAuth callback lands here with ?result=…
  validateSearch: (raw: Record<string, unknown>): { result?: Result } => ({
    result: RESULTS.find((r) => r === raw.result),
  }),
  component: FortnoxPage,
});

/** Connecting Cashflow to Fortnox, for the treasurer; others with view-all see the status. */
function FortnoxPage() {
  const t = useT();
  const f = t.fortnox;
  const locale = useLocale();
  const { result } = Route.useSearch();
  const navigate = Route.useNavigate();
  const status = useQuery(getFortnoxStatus, {});
  const me = useQuery(getMe, {});
  const canManage = Boolean(me.data?.capabilities?.manageFortnox);
  const [confirming, setConfirming] = useState(false);
  const queryClient = useQueryClient();
  const transport = useTransport();
  const disconnect = useMutation(disconnectFortnox, {
    onSuccess: () => {
      toast.success(f.disconnected);
      void queryClient.invalidateQueries({
        queryKey: createConnectQueryKey({ schema: getFortnoxStatus, transport, cardinality: undefined }),
      });
    },
    onError: (error) => toast.error(problemMessage(error, t)),
  });

  // Say how connecting went, once, then drop the parameter.
  useEffect(() => {
    if (!result) return;
    if (result === "connected") toast.success(f.result.connected);
    else toast.error(f.result[result]);
    void navigate({ search: {}, replace: true });
  }, [result, navigate, f]);

  const connectLink = (label: string, variant: "default" | "outline" = "default") =>
    // A full page load: the server redirects to Fortnox.
    canManage && (
      <a href="/fortnox/auth" className={buttonVariants({ variant })}>
        <PlugZap /> {label}
      </a>
    );

  const body = () => {
    if (!status.data) return <Skeleton className="h-36 rounded-xl" />;
    const s = status.data;
    if (!s.enabled) return <StateCard icon={<Power />} title={f.disabledTitle} description={f.disabledBody} />;
    if (!s.connected) {
      return (
        <StateCard
          icon={<Landmark />}
          title={f.notConnectedTitle}
          description={
            <>
              {f.notConnectedBody} {canManage ? f.howItWorks : f.viewOnly}
            </>
          }
          action={connectLink(f.connect)}
        />
      );
    }
    const since = s.connectedAt
      ? new Intl.DateTimeFormat(intlLocale[locale], { dateStyle: "medium" }).format(timestampDate(s.connectedAt))
      : "";
    return (
      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <CircleCheckBig className="size-8 shrink-0 text-primary" aria-hidden />
          <div className="flex min-w-0 flex-1 flex-col gap-0.5">
            <h2 className="font-medium">{f.connectedTitle}</h2>
            <p className="text-muted-foreground text-sm">{f.connectedBy(s.connectedBy?.name ?? "", since)}</p>
            {!canManage && <p className="text-muted-foreground text-xs">{f.viewOnly}</p>}
          </div>
          {canManage && (
            <div className="flex flex-wrap gap-2">
              {connectLink(f.reconnect, "outline")}
              <Button variant="outline" onClick={() => setConfirming(true)} disabled={disconnect.isPending}>
                {disconnect.isPending ? <Loader2 className="animate-spin" /> : <Power />} {f.disconnect}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Page
      title={t.nav.fortnox}
      actions={
        <ButtonLink variant="outline" size="sm" to="/vouchers">
          <ScrollText /> {f.vouchersLink}
        </ButtonLink>
      }
    >
      <div className="max-w-3xl">{body()}</div>
      <AlertDialog open={confirming} onOpenChange={setConfirming}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{f.disconnectTitle}</AlertDialogTitle>
            <AlertDialogDescription>{f.disconnectBody}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.claim.cancel}</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={() => disconnect.mutate({})}>
              <Power /> {f.disconnect}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Page>
  );
}
