import { useQuery } from "@connectrpc/connect-query";
import { useHotkey } from "@tanstack/react-hotkeys";
import { useNavigate, useRouter } from "@tanstack/react-router";
import {
  ArrowRight,
  BadgeCheck,
  Banknote,
  CircleCheckBig,
  Ellipsis,
  Flag,
  FlagOff,
  Hourglass,
  Loader2,
  Pencil,
  Stamp,
  Trash2,
  Undo2,
} from "lucide-react";
import { useState } from "react";
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
import { Button } from "#/components/ui/button";
import { ButtonLink } from "#/components/ui/button-link";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "#/components/ui/dropdown-menu";
import { type Claim, ClaimKind } from "#/gen/cashflow/claim/v1/claim_pb";
import { listClaims } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import type { Capabilities } from "#/gen/cashflow/user/v1/user_pb";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { claimEditLink, claimLink, formatDate, type QueueSlug, queueToProto } from "#/lib/claims";
import { type Messages, useLocale, useT } from "#/lib/i18n";
import { cn } from "#/lib/utils";
import { useClaimAction } from "./use-claim-action";

type Tone = "warning" | "waiting" | "ready" | "done";

/**
 * Where the claim stands and who acts next, in plain words for this viewer:
 * what they can do now, or who everyone is waiting for, and why an action
 * they might expect is not available.
 */
function describe(
  claim: Claim,
  me: string,
  caps: Capabilities | undefined,
  t: Messages,
  locale: ReturnType<typeof useLocale>,
) {
  const s = claim.summary;
  const st = s?.status;
  const a = claim.actions;
  if (!s || !st || !a) return { tone: "waiting" as Tone, lines: [] as string[] };
  const n = t.claim.nextStep;
  const isOwner = s.owner?.username === me;
  const isExpense = s.kind === ClaimKind.EXPENSE;

  if (st.flagged) {
    const lines = [isOwner ? n.flaggedOwner : n.flagged(s.owner?.name ?? "")];
    if (!isOwner && (caps?.attestAny || caps?.confirm)) lines.push(n.flaggedBlocks);
    return { tone: "warning" as Tone, lines };
  }
  if (!st.attested) {
    const waiting = [...new Set(claim.parts.filter((p) => !p.attestedBy).map((p) => p.costCentre))];
    const lines = [n.attest(waiting.join(", "))];
    const couldAttest = waiting.some(
      (cc) => caps?.attestAll || caps?.attestCostCentres.some((x) => x.toLowerCase() === cc.toLowerCase()),
    );
    if (a.attestPartIds.length > 0) lines.push(n.attestYou);
    else if (isOwner && isExpense && couldAttest) lines.push(n.ownExpense);
    return { tone: "waiting" as Tone, lines };
  }
  if (isExpense && !st.confirmed) {
    return { tone: "waiting" as Tone, lines: [n.confirm, ...(a.confirm ? [n.confirmYou] : [])] };
  }
  if (!st.paid) {
    if (isExpense) return { tone: "ready" as Tone, lines: [n.pay, ...(caps?.pay ? [n.payoutYou] : [])] };
    return { tone: "ready" as Tone, lines: [n.payInvoice, ...(a.pay ? [n.payYou] : [])] };
  }
  if (!st.verification) {
    const paidOn = claim.payment?.date || claim.paidAt;
    return { tone: "waiting" as Tone, lines: [n.account(formatDate(paidOn, locale))] };
  }
  return { tone: "done" as Tone, lines: [n.done(st.verification)] };
}

const toneStyle: Record<Tone, { box: string; icon: typeof Hourglass }> = {
  warning: { box: "border-destructive/30 bg-destructive/5", icon: Flag },
  waiting: { box: "border-border bg-muted/50", icon: Hourglass },
  ready: { box: "border-primary/30 bg-primary/5", icon: Banknote },
  done: { box: "border-primary/30 bg-primary/5", icon: CircleCheckBig },
};

export function NextStep({ claim, queue }: { claim: Claim; queue?: QueueSlug }) {
  const t = useT();
  const locale = useLocale();
  const me = useQuery(getMe, {});
  const s = claim.summary;
  const a = claim.actions;
  const { client, run, pending } = useClaimAction(s?.kind ?? ClaimKind.EXPENSE, s?.number ?? 0n);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const router = useRouter();
  if (!s || !a) return null;

  const { tone, lines } = describe(claim, me.data?.user?.username ?? "", me.data?.capabilities, t, locale);
  const ToneIcon = toneStyle[tone].icon;
  const ref = { kind: s.kind, number: s.number };
  const act = t.claim.actions;
  const done = t.claim.done;

  const attestAll = () =>
    run({
      key: "attest",
      done: done.attest,
      // One part at a time: each is checked and commented on its own.
      call: async () => {
        let last: Awaited<ReturnType<typeof client.setPartAttested>> | undefined;
        for (const partId of a.attestPartIds) {
          last = await client.setPartAttested({ claim: ref, partId, attested: true });
        }
        return last ?? {};
      },
    });

  // With one part, undoing its attestation lives here; several parts have their own buttons.
  const unattestSingle = claim.parts.length === 1 ? a.unattestPartIds[0] : undefined;
  const hasMore = unattestSingle !== undefined || a.unconfirm || a.flag || a.unflag || a.delete;

  return (
    <section
      aria-labelledby="next-step"
      className={cn("flex flex-col gap-4 rounded-xl border p-4 md:flex-row md:items-center", toneStyle[tone].box)}
    >
      <div className="flex min-w-0 flex-1 gap-3">
        <ToneIcon
          aria-hidden
          className={cn("mt-0.5 size-5 shrink-0", tone === "warning" ? "text-destructive" : "text-primary")}
        />
        <div className="flex flex-col gap-0.5">
          <h2 id="next-step" className="sr-only">
            {t.claim.nextStep.title}
          </h2>
          {lines.map((line, i) => (
            <p key={line} className={cn("text-sm", i === 0 ? "font-medium" : "text-muted-foreground")}>
              {line}
            </p>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {a.attestPartIds.length > 0 && (
          <Button onClick={attestAll} disabled={pending !== undefined}>
            {pending === "attest" ? <Loader2 className="animate-spin" /> : <Stamp />}
            {a.attestPartIds.length > 1 && a.attestPartIds.length < claim.parts.length ? act.attestAll : act.attest}
          </Button>
        )}
        {a.confirm && (
          <Button
            disabled={pending !== undefined}
            onClick={() =>
              run({
                key: "confirm",
                done: done.confirm,
                call: () => client.setConfirmed({ number: s.number, confirmed: true }),
              })
            }
          >
            {pending === "confirm" ? <Loader2 className="animate-spin" /> : <BadgeCheck />}
            {act.confirm}
          </Button>
        )}
        {a.edit && (
          // Fixing a flagged expense is the owner's next step, so it leads then.
          <ButtonLink variant={s.status?.flagged ? "default" : "outline"} {...claimEditLink(s.kind, s.number)}>
            <Pencil /> {s.status?.flagged ? act.fix : act.edit}
          </ButtonLink>
        )}
        {a.pay && (
          <Button
            disabled={pending !== undefined}
            onClick={() => run({ key: "pay", done: done.pay, call: () => client.payInvoice({ number: s.number }) })}
          >
            {pending === "pay" ? <Loader2 className="animate-spin" /> : <Banknote />}
            {act.pay}
          </Button>
        )}

        {hasMore && (
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button variant="outline">
                  <Ellipsis /> {t.claim.more}
                </Button>
              }
            />
            <DropdownMenuContent align="end" className="min-w-52">
              {unattestSingle !== undefined && (
                <DropdownMenuItem
                  onClick={() =>
                    run({
                      key: "unattest",
                      done: done.unattest,
                      call: () => client.setPartAttested({ claim: ref, partId: unattestSingle, attested: false }),
                    })
                  }
                >
                  <Undo2 /> {act.unattest}
                </DropdownMenuItem>
              )}
              {a.unconfirm && (
                <DropdownMenuItem
                  onClick={() =>
                    run({
                      key: "unconfirm",
                      done: done.unconfirm,
                      call: () => client.setConfirmed({ number: s.number, confirmed: false }),
                    })
                  }
                >
                  <Undo2 /> {act.unconfirm}
                </DropdownMenuItem>
              )}
              {a.flag && (
                <DropdownMenuItem
                  title={t.claim.flagHint}
                  onClick={() =>
                    run({
                      key: "flag",
                      done: done.flag,
                      call: () => client.setFlagged({ number: s.number, flagged: true }),
                    })
                  }
                >
                  <Flag /> {act.flag}
                </DropdownMenuItem>
              )}
              {a.unflag && (
                <DropdownMenuItem
                  onClick={() =>
                    run({
                      key: "unflag",
                      done: done.unflag,
                      call: () => client.setFlagged({ number: s.number, flagged: false }),
                    })
                  }
                >
                  <FlagOff /> {act.unflag}
                </DropdownMenuItem>
              )}
              {a.delete && (
                <>
                  {(unattestSingle !== undefined || a.unconfirm || a.flag || a.unflag) && <DropdownMenuSeparator />}
                  <DropdownMenuItem variant="destructive" onClick={() => setConfirmDelete(true)}>
                    <Trash2 /> {act.delete}
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {queue && <NextInQueue queue={queue} current={s.number} kind={s.kind} />}
      </div>

      <AlertDialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t.claim.deleteTitle}</AlertDialogTitle>
            <AlertDialogDescription>{t.claim.deleteBody(s.description)}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t.claim.cancel}</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              onClick={async () => {
                const deleted = await run({
                  key: "delete",
                  done: done.delete,
                  call: () => client.deleteClaim({ claim: ref }),
                });
                if (deleted) {
                  if (router.history.canGoBack()) router.history.back();
                  else void router.navigate({ to: "/" });
                }
              }}
            >
              <Trash2 /> {act.delete}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}

/**
 * The next claim in the queue the user came from, so a queue can be worked
 * through without going back to the list. N jumps there too.
 */
function NextInQueue({ queue, current, kind }: { queue: QueueSlug; current: bigint; kind: ClaimKind }) {
  const t = useT();
  const navigate = useNavigate();
  const { data } = useQuery(listClaims, { queue: queueToProto[queue], pageSize: 5 });
  const next = data?.claims.find((c) => !(c.number === current && c.kind === kind));
  const link = next ? { ...claimLink(next.kind, next.number), search: { queue } } : undefined;
  useHotkey("N", () => link && void navigate(link), { enabled: Boolean(link) });

  if (!link) {
    return (
      <span className="flex items-center gap-1.5 px-2 text-muted-foreground text-sm">
        <CircleCheckBig className="size-4 text-primary" /> {t.claim.actions.queueDone}
      </span>
    );
  }
  return (
    <ButtonLink variant="outline" {...link}>
      {t.claim.actions.next} <ArrowRight />
    </ButtonLink>
  );
}
