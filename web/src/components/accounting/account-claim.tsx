import { Code, ConnectError } from "@connectrpc/connect";
import {
  createConnectQueryKey,
  createQueryOptions,
  useQuery,
  useSuspenseQuery,
  useTransport,
} from "@connectrpc/connect-query";
import { type QueryClient, useQueryClient } from "@tanstack/react-query";
import { Navigate, useNavigate } from "@tanstack/react-router";
import { BookCheck, ChevronDown, Landmark, PlugZap } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { BackButton } from "#/components/claim/claim-detail";
import { loadClaim } from "#/components/claim/claim-route";
import { FilesViewer } from "#/components/claim/files-viewer";
import { NextInQueue } from "#/components/claim/next-step";
import { Amount, CostCentreChip, KindIcon, StageBadge } from "#/components/claims/badges";
import { StateCard } from "#/components/layout/states";
import { UserAvatar } from "#/components/layout/user-avatar";
import { ButtonLink } from "#/components/ui/button-link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "#/components/ui/card";
import { Skeleton } from "#/components/ui/skeleton";
import { type AccountClaimResponse, AccountingService } from "#/gen/cashflow/accounting/v1/accounting_pb";
import {
  getVoucherDraft,
  listFortnoxAccounts,
  listFortnoxCostCentres,
} from "#/gen/cashflow/accounting/v1/accounting-AccountingService_connectquery";
import { type Claim, type ClaimKind, ClaimService, Queue } from "#/gen/cashflow/claim/v1/claim_pb";
import { getClaim, listClaims } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { claimAccountLink, claimLink, formatDate, kindSlug, type QueueSlug } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";
import { transport } from "#/lib/rpc";
import { cn } from "#/lib/utils";
import { ManualVoucher } from "./manual-voucher";
import { VoucherForm } from "./voucher-form";

// Fortnox's chart of accounts changes rarely; the server caches it too.
const LISTS_STALE = 60 * 60 * 1000;

/** Loads the claim and its voucher draft together, so the page opens complete. */
export async function loadAccounting(queryClient: QueryClient, kind: ClaimKind, number: bigint) {
  await Promise.all([
    loadClaim(queryClient, kind, number),
    // Without permission there is no draft; the page explains instead.
    queryClient
      .ensureQueryData(createQueryOptions(getVoucherDraft, { claim: { kind, number } }, { transport }))
      .catch((error) => {
        if (ConnectError.from(error).code !== Code.PermissionDenied) throw error;
      }),
  ]);
}

/**
 * Booking one claim, all on one screen: what it is, the voucher to book in
 * Fortnox or the number of one booked by hand, and the receipt beside it.
 * Opened from the bookkeeping queue, it moves on to the next claim after.
 */
export function AccountClaim({ kind, number, queue }: { kind: ClaimKind; number: bigint; queue?: QueueSlug }) {
  const t = useT();
  const a = t.accounting;
  const { data } = useSuspenseQuery(getClaim, { kind, number });
  const claim = data.claim;
  const s = claim?.summary;
  const me = useQuery(getMe, {});
  const draft = useQuery(getVoucherDraft, { claim: { kind, number } }, { enabled: Boolean(claim?.actions?.account) });
  const fortnoxOn = Boolean(draft.data?.fortnoxAvailable);
  const accounts = useQuery(listFortnoxAccounts, {}, { enabled: fortnoxOn, staleTime: LISTS_STALE });
  const costCentres = useQuery(listFortnoxCostCentres, {}, { enabled: fortnoxOn, staleTime: LISTS_STALE });
  const onBooked = useOnBooked(kind, number, queue);
  const [manualOpen, setManualOpen] = useState(false);
  if (!claim || !s) throw new Error("GetClaim returned no claim");
  // Someone who may see but not book it (a view-all admin in the queue) gets
  // the ordinary claim page, which says who books it.
  if (!claim.actions?.account && !s.status?.verification) return <Navigate {...claimLink(kind, number)} replace />;

  const body = () => {
    if (!claim.actions?.account) {
      return (
        <StateCard
          icon={<BookCheck />}
          title={a.alreadyTitle}
          description={a.alreadyBody(s.status?.verification ?? "")}
          action={<ButtonLink {...claimLink(kind, number)}>{a.backToClaim}</ButtonLink>}
        />
      );
    }
    if (!draft.data) return <Skeleton className="h-64 rounded-xl" />;
    const manual = (
      <ManualVoucher kind={kind} number={number} draft={draft.data} onBooked={onBooked} onProblem={toast.error} />
    );
    if (!fortnoxOn) {
      const enabled = me.data?.features?.fortnox;
      return (
        <Card size="sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PlugZap className="size-4 text-warning-ink" /> {enabled ? a.notConnected : a.disabled}
            </CardTitle>
            {enabled && (
              <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-1">
                {a.notConnectedAsk}
                {me.data?.capabilities?.manageFortnox && (
                  <ButtonLink size="xs" variant="outline" to="/fortnox">
                    <Landmark /> {a.notConnectedManage}
                  </ButtonLink>
                )}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>{manual}</CardContent>
        </Card>
      );
    }
    return (
      <>
        <Card size="sm">
          <CardHeader>
            <CardTitle>{a.fortnoxTitle}</CardTitle>
            <CardDescription className="text-xs">{a.fortnoxHelp}</CardDescription>
          </CardHeader>
          <CardContent>
            {accounts.data && costCentres.data ? (
              <VoucherForm
                kind={kind}
                number={number}
                draft={draft.data}
                accounts={accounts.data.accounts}
                costCentres={costCentres.data.costCentres}
                onBooked={onBooked}
                onProblem={toast.error}
              />
            ) : (
              <div className="flex flex-col gap-2" aria-busy="true">
                <span className="sr-only">{a.loading}</span>
                <Skeleton className="h-9" />
                <Skeleton className="h-9" />
                <Skeleton className="h-9" />
              </div>
            )}
          </CardContent>
        </Card>
        <Card size="sm">
          <CardHeader>
            <button
              type="button"
              aria-expanded={manualOpen}
              onClick={() => setManualOpen((open) => !open)}
              className="-m-1 flex items-center gap-1.5 rounded p-1 text-left font-medium text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <ChevronDown className={cn("size-4 transition-transform", !manualOpen && "-rotate-90")} />
              {a.manualTitle}
            </button>
          </CardHeader>
          {manualOpen && <CardContent>{manual}</CardContent>}
        </Card>
      </>
    );
  };

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-3 md:px-6 md:py-4">
      <div className="flex items-center justify-between gap-2">
        <BackButton />
        {/* Skipping one: booking moves on by itself. */}
        {queue && <NextInQueue queue={queue} current={number} kind={kind} size="sm" />}
      </div>
      <div className="mt-2 grid items-start gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
        <div className="flex flex-col gap-3">
          <Header claim={claim} />
          {body()}
        </div>
        <div className="lg:sticky lg:top-4">
          <FilesViewer files={claim.files} />
        </div>
      </div>
    </main>
  );
}

function Header({ claim }: { claim: Claim }) {
  const t = useT();
  const locale = useLocale();
  const s = claim.summary;
  if (!s) return null;
  return (
    <Card size="sm" className="receipt-edge rounded-b-none">
      <CardContent className="flex flex-col gap-2">
        <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
          <KindIcon kind={s.kind} />
          {t.accounting.heading(t.claims.kind[kindSlug(s.kind)], s.number.toString())}
          <ButtonLink variant="link" size="xs" className="ml-auto h-auto px-0" {...claimLink(s.kind, s.number)}>
            {t.accounting.openClaim}
          </ButtonLink>
        </div>
        <div className="flex flex-wrap items-baseline justify-between gap-x-4">
          <h1 className="min-w-0 font-display font-semibold text-xl tracking-tight">{s.description}</h1>
          <Amount ore={s.amountOre} className="font-medium text-xl" />
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm">
          {s.owner && (
            <span className="flex items-center gap-2">
              <UserAvatar name={s.owner.name} username={s.owner.username} className="bg-secondary" />
              <span className="font-medium">{s.owner.name}</span>
            </span>
          )}
          <span className="text-muted-foreground">{formatDate(s.date, locale)}</span>
          <StageBadge status={s.status} />
          <span className="flex flex-wrap gap-1">
            {s.costCentres.map((cc) => (
              <CostCentreChip key={cc} name={cc} />
            ))}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * After booking: the claim's cache is updated from the answer, lists refetch,
 * and the user moves on: to the next claim in the queue they came from (or
 * the empty queue), or back to the claim.
 */
function useOnBooked(kind: ClaimKind, number: bigint, queue?: QueueSlug) {
  const t = useT();
  const queryClient = useQueryClient();
  const transport = useTransport();
  const navigate = useNavigate();
  return async (result: AccountClaimResponse) => {
    queryClient.setQueryData(
      createConnectQueryKey({ schema: getClaim, input: { kind, number }, transport, cardinality: "finite" }),
      { $typeName: "cashflow.claim.v1.GetClaimResponse", claim: result.claim },
    );
    for (const schema of [ClaimService, AccountingService]) {
      void queryClient.invalidateQueries({
        queryKey: createConnectQueryKey({ schema, transport, cardinality: undefined }),
        predicate: (query) => (query.queryKey[1] as { methodName?: string })?.methodName !== getClaim.name,
      });
    }
    toast.success(t.accounting.booked(result.voucherNumber));

    if (queue !== "account") {
      void navigate({ ...claimLink(kind, number), replace: true });
      return;
    }
    const { claims } = await queryClient.fetchQuery(
      createQueryOptions(listClaims, { queue: Queue.ACCOUNT, pageSize: 5 }, { transport }),
    );
    const next = claims.find((c) => !(c.kind === kind && c.number === number));
    if (next) void navigate({ ...claimAccountLink(next.kind, next.number), search: { queue } });
    else {
      toast.success(t.accounting.queueDone);
      void navigate({ to: "/account" });
    }
  };
}
