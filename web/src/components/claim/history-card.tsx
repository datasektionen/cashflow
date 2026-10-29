import { Loader2, Send } from "lucide-react";
import { Fragment, useState } from "react";
import { UserAvatar } from "#/components/layout/user-avatar";
import { Button } from "#/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import { Kbd } from "#/components/ui/kbd";
import { Textarea } from "#/components/ui/textarea";
import type { Claim } from "#/gen/cashflow/claim/v1/claim_pb";
import { intlLocale, useLocale, useT } from "#/lib/i18n";
import { useClaimAction } from "./use-claim-action";

/**
 * Cashflow 3 wrote workflow steps as comments, quoting things in ```triple
 * backticks```; those are shown as code instead of raw backticks.
 */
export function CommentBody({ body }: { body: string }) {
  const pieces = body.split(/```([\s\S]*?)```/g);
  return (
    <p className="whitespace-pre-wrap break-words text-sm">
      {pieces.map((piece, i) =>
        i % 2 === 1 ? (
          // biome-ignore lint/suspicious/noArrayIndexKey: pieces of one static string
          <code key={i} className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">
            {piece}
          </code>
        ) : (
          // biome-ignore lint/suspicious/noArrayIndexKey: pieces of one static string
          <Fragment key={i}>{piece}</Fragment>
        ),
      )}
    </p>
  );
}

export function HistoryCard({ claim }: { claim: Claim }) {
  const t = useT();
  const comments = claim.comments;
  const locale = useLocale();
  const format = new Intl.DateTimeFormat(intlLocale[locale], { dateStyle: "medium", timeStyle: "short" });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t.claim.history}</CardTitle>
      </CardHeader>
      <CardContent>
        {comments.length === 0 ? (
          <p className="text-muted-foreground text-sm">{t.claim.noComments}</p>
        ) : (
          <ol className="flex flex-col gap-3">
            {comments.map((comment, i) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: comments have no id and never reorder
              <li key={i} className="flex gap-3">
                <UserAvatar
                  name={comment.author?.name ?? "?"}
                  username={comment.author?.username}
                  className="bg-secondary text-secondary-foreground"
                />
                <div className="flex min-w-0 flex-col gap-0.5">
                  <div className="flex flex-wrap items-baseline gap-x-2">
                    <span className="font-medium text-sm">{comment.author?.name}</span>
                    {comment.createdAt && (
                      <time
                        className="text-muted-foreground text-xs"
                        dateTime={new Date(Number(comment.createdAt.seconds) * 1000).toISOString()}
                      >
                        {format.format(new Date(Number(comment.createdAt.seconds) * 1000))}
                      </time>
                    )}
                  </div>
                  <CommentBody body={comment.body} />
                </div>
              </li>
            ))}
          </ol>
        )}
        <CommentBox claim={claim} />
      </CardContent>
    </Card>
  );
}

/** Write a comment; Ctrl/Cmd+Enter sends. The text stays if sending fails. */
function CommentBox({ claim }: { claim: Claim }) {
  const t = useT();
  const [body, setBody] = useState("");
  const s = claim.summary;
  const { client, run, pending } = useClaimAction(s?.kind ?? 0, s?.number ?? 0n);
  if (!s) return null;

  const send = async () => {
    if (!body.trim() || pending) return;
    const sent = await run({
      key: "comment",
      done: t.claim.done.comment,
      call: () => client.addComment({ claim: { kind: s.kind, number: s.number }, body }),
    });
    if (sent) setBody("");
  };

  return (
    <form
      className="mt-6 flex flex-col gap-2 border-t pt-4"
      onSubmit={(event) => {
        event.preventDefault();
        void send();
      }}
    >
      <Textarea
        value={body}
        onChange={(event) => setBody(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) void send();
        }}
        placeholder={t.claim.commentPlaceholder}
        aria-label={t.claim.commentPlaceholder}
        rows={2}
        className="min-h-16 resize-y"
      />
      <div className="flex items-center justify-between gap-2">
        <span className="text-muted-foreground text-xs">{t.claim.commentHint}</span>
        <Button type="submit" size="sm" disabled={!body.trim() || pending !== undefined}>
          {pending === "comment" ? <Loader2 className="animate-spin" /> : <Send />}
          {t.claim.send}
          <Kbd className="hidden bg-primary-foreground/15 text-primary-foreground sm:inline-flex">
            {t.claim.sendShortcut}
          </Kbd>
        </Button>
      </div>
    </form>
  );
}
