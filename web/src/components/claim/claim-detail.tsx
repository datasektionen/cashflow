import { useQuery, useSuspenseQuery } from "@connectrpc/connect-query";
import { Link, useCanGoBack, useRouter } from "@tanstack/react-router";
import { ArrowLeft } from "lucide-react";
import { Amount, CostCentreChip, KindIcon } from "#/components/claims/badges";
import { UserAvatar } from "#/components/layout/user-avatar";
import { Button } from "#/components/ui/button";
import { Card, CardContent } from "#/components/ui/card";
import { Separator } from "#/components/ui/separator";
import { type Claim, ClaimKind, type Person, Stage } from "#/gen/cashflow/claim/v1/claim_pb";
import { getClaim } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { formatDate, kindSlug, type QueueSlug, stageSlug } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";
import { canLookUpUsers } from "#/lib/navigation";
import { FilesViewer } from "./files-viewer";
import { HistoryCard } from "./history-card";
import { NextStep } from "./next-step";
import { PartsCard } from "./parts-card";
import { StageTimeline } from "./stage-timeline";

/** One expense or invoice in full: the claim on the left, its receipts beside it. */
export function ClaimDetail({ kind, number, queue }: { kind: ClaimKind; number: bigint; queue?: QueueSlug }) {
  const { data } = useSuspenseQuery(getClaim, { kind, number });
  const claim = data.claim;
  if (!claim?.summary) throw new Error("GetClaim returned no claim");

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-3 md:px-6 md:py-4">
      <BackButton />
      {/*
        One files viewer, placed by the grid: after the header on small screens
        (the receipt is what people look at first), and in its own sticky
        column beside everything on large ones.
      */}
      <div className="mt-2 grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
        <div className="flex flex-col gap-3 lg:col-start-1">
          <HeaderCard claim={claim} />
          <NextStep claim={claim} queue={queue} />
        </div>
        <div className="lg:sticky lg:top-4 lg:col-start-2 lg:row-span-3 lg:row-start-1">
          <FilesViewer files={claim.files} />
        </div>
        <div className="lg:col-start-1">
          <PartsCard claim={claim} />
        </div>
        <div className="lg:col-start-1">
          <HistoryCard claim={claim} />
        </div>
      </div>
    </main>
  );
}

/** Back to wherever the user came from (keeping that list's filters), or home. */
export function BackButton() {
  const t = useT();
  const router = useRouter();
  const canGoBack = useCanGoBack();
  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-2 h-7 text-muted-foreground"
      onClick={() => (canGoBack ? router.history.back() : void router.navigate({ to: "/" }))}
    >
      <ArrowLeft /> {t.claim.backTo(canGoBack ? t.claim.previousPage : t.nav.overview)}
    </Button>
  );
}

function HeaderCard({ claim }: { claim: Claim }) {
  const t = useT();
  const locale = useLocale();
  const s = claim.summary;
  if (!s?.status) return null;
  const stage = s.status.stage;
  const isInvoice = s.kind === ClaimKind.INVOICE;

  const facts: Array<[string, string]> = [
    [isInvoice ? t.claim.invoiceDate : t.claim.expenseDate, formatDate(s.date, locale)],
    ...(isInvoice
      ? ([
          [t.claim.invoiceNumber, claim.invoiceNumber],
          [t.claim.dueDate, formatDate(claim.dueDate, locale)],
        ] as Array<[string, string]>)
      : []),
    [t.claim.verification, s.status.verification],
  ];

  return (
    <Card className="receipt-edge relative overflow-hidden rounded-b-none">
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
          <KindIcon kind={s.kind} />
          {t.claims.kind[kindSlug(s.kind)]}
          <span className="amount">#{s.number.toString()}</span>
          {/* The furthest step reached, stamped onto the receipt. */}
          {stage > Stage.SUBMITTED && !s.status.flagged && (
            <span key={stage} className="stamp animate-stamp ml-auto text-primary text-xs" aria-hidden>
              {t.claims.stamp[stageSlug[stage]]}
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h1 className="min-w-0 font-display font-semibold text-xl tracking-tight md:text-2xl">{s.description}</h1>
          <Amount ore={s.amountOre} className="font-medium text-2xl" />
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
          {s.owner && (
            <span className="flex items-center gap-2">
              <UserAvatar
                name={s.owner.name}
                username={s.owner.username}
                className="bg-secondary text-secondary-foreground"
              />
              <span className="flex flex-col leading-tight">
                <OwnerName owner={s.owner} />
                <span className="text-muted-foreground text-xs">
                  {t.claim.submittedOn(formatDate(s.createdDate, locale))}
                </span>
              </span>
            </span>
          )}
          <dl className="flex flex-wrap gap-x-5 gap-y-2">
            {facts
              .filter(([, value]) => value)
              .map(([label, value]) => (
                <div key={label} className="flex flex-col leading-tight">
                  <dt className="text-muted-foreground text-xs">{label}</dt>
                  <dd className="font-medium">{value}</dd>
                </div>
              ))}
          </dl>
          {s.costCentres.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {s.costCentres.map((cc) => (
                <CostCentreChip key={cc} name={cc} />
              ))}
            </div>
          )}
        </div>

        <Separator />
        <StageTimeline claim={claim} />
      </CardContent>
    </Card>
  );
}

/** The owner, linking to their page for those who may see it. */
function OwnerName({ owner }: { owner: Person }) {
  const t = useT();
  const caps = useQuery(getMe, {}).data?.capabilities;
  if (!caps || !canLookUpUsers(caps)) return <span className="font-medium">{owner.name}</span>;
  return (
    <Link
      to="/users/$username"
      params={{ username: owner.username }}
      title={t.users.view(owner.name)}
      className="font-medium underline-offset-2 hover:underline"
    >
      {owner.name}
    </Link>
  );
}
