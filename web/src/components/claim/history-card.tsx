import { Fragment } from "react";
import { UserAvatar } from "#/components/layout/user-avatar";
import { Card, CardContent, CardHeader, CardTitle } from "#/components/ui/card";
import type { Comment } from "#/gen/cashflow/claim/v1/claim_pb";
import { intlLocale, useLocale, useT } from "#/lib/i18n";

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

export function HistoryCard({ comments }: { comments: Comment[] }) {
  const t = useT();
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
          <ol className="flex flex-col gap-5">
            {comments.map((comment, i) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: comments have no id and never reorder
              <li key={i} className="flex gap-3">
                <UserAvatar name={comment.author?.name ?? "?"} className="bg-secondary text-secondary-foreground" />
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
      </CardContent>
    </Card>
  );
}
