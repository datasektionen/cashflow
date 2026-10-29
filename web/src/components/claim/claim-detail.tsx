import { useSuspenseQuery } from "@connectrpc/connect-query";
import { useCanGoBack, useRouter } from "@tanstack/react-router";
import { ArrowLeft, Flag } from "lucide-react";
import { Amount, CostCentreChip, KindIcon } from "#/components/claims/badges";
import { UserAvatar } from "#/components/layout/user-avatar";
import { Alert, AlertDescription, AlertTitle } from "#/components/ui/alert";
import { Button } from "#/components/ui/button";
import { Card, CardContent } from "#/components/ui/card";
import { Separator } from "#/components/ui/separator";
import { type Claim, ClaimKind, Stage } from "#/gen/cashflow/claim/v1/claim_pb";
import { getClaim } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import { formatDate, kindSlug, stageSlug } from "#/lib/claims";
import { useLocale, useT } from "#/lib/i18n";
import { FilesViewer } from "./files-viewer";
import { HistoryCard } from "./history-card";
import { PartsCard } from "./parts-card";
import { StageTimeline } from "./stage-timeline";

/** One expense or invoice in full: the claim on the left, its receipts beside it. */
export function ClaimDetail({ kind, number }: { kind: ClaimKind; number: bigint }) {
  const { data } = useSuspenseQuery(getClaim, { kind, number });
  const claim = data.claim;
  if (!claim?.summary) throw new Error("GetClaim returned no claim");

  return (
    <main className="mx-auto w-full max-w-7xl p-4 md:p-8">
      <BackButton />
      {/*
        One files viewer, placed by the grid: after the header on small screens
        (the receipt is what people look at first), and in its own sticky
        column beside everything on large ones.
      */}
      <div className="mt-4 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
        {claim.summary.status?.flagged && (
          <div className="lg:col-start-1">
            <FlaggedAlert />
          </div>
        )}
        <div className="lg:col-start-1">
          <HeaderCard claim={claim} />
        </div>
        <div className="lg:sticky lg:top-6 lg:col-start-2 lg:row-span-4 lg:row-start-1">
          <FilesViewer files={claim.files} />
        </div>
        <div className="lg:col-start-1">
          <PartsCard parts={claim.parts} total={claim.summary.amountOre} />
        </div>
        <div className="lg:col-start-1">
          <HistoryCard comments={claim.comments} />
        </div>
      </div>
    </main>
  );
}

/** Back to wherever the user came from (keeping that list's filters), or home. */
function BackButton() {
  const t = useT();
  const router = useRouter();
  const canGoBack = useCanGoBack();
  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-2 text-muted-foreground"
      onClick={() => (canGoBack ? router.history.back() : void router.navigate({ to: "/" }))}
    >
      <ArrowLeft /> {t.claim.backTo(canGoBack ? t.claim.previousPage : t.nav.overview)}
    </Button>
  );
}

function FlaggedAlert() {
  const t = useT();
  return (
    <Alert variant="destructive">
      <Flag />
      <AlertTitle>{t.claim.flaggedTitle}</AlertTitle>
      <AlertDescription>{t.claim.flaggedBody}</AlertDescription>
    </Alert>
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
      {/* The furthest step reached, stamped onto the receipt. */}
      {stage > Stage.SUBMITTED && !s.status.flagged && (
        <span key={stage} className="stamp animate-stamp absolute top-5 right-5 text-primary text-sm" aria-hidden>
          {t.claims.stamp[stageSlug[stage]]}
        </span>
      )}
      <CardContent className="flex flex-col gap-5">
        <div className="flex flex-col gap-2 pr-28">
          <span className="flex items-center gap-1.5 text-muted-foreground text-sm">
            <KindIcon kind={s.kind} />
            {t.claims.kind[kindSlug(s.kind)]}
            <span className="amount">#{s.number.toString()}</span>
          </span>
          <h1 className="font-display font-semibold text-2xl tracking-tight md:text-3xl">{s.description}</h1>
          <Amount ore={s.amountOre} className="font-medium text-3xl md:text-4xl" />
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
          {s.owner && (
            <span className="flex items-center gap-2">
              <UserAvatar name={s.owner.name} className="bg-secondary text-secondary-foreground" />
              <span className="flex flex-col leading-tight">
                <span className="font-medium">{s.owner.name}</span>
                <span className="text-muted-foreground text-xs">
                  {t.claim.submittedOn(formatDate(s.createdDate, locale))}
                </span>
              </span>
            </span>
          )}
          <dl className="flex flex-wrap gap-x-6 gap-y-2">
            {facts
              .filter(([, value]) => value)
              .map(([label, value]) => (
                <div key={label} className="flex flex-col leading-tight">
                  <dt className="text-muted-foreground text-xs">{label}</dt>
                  <dd className="font-medium">{value}</dd>
                </div>
              ))}
          </dl>
        </div>

        {s.costCentres.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {s.costCentres.map((cc) => (
              <CostCentreChip key={cc} name={cc} />
            ))}
          </div>
        )}

        <Separator />
        <StageTimeline claim={claim} />
      </CardContent>
    </Card>
  );
}
