import type { ErrorComponentProps } from "@tanstack/react-router";
import { useRouter } from "@tanstack/react-router";
import { Construction, FileQuestion, TriangleAlert } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "#/components/ui/button";
import { ButtonLink } from "#/components/ui/button-link";
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyMedia, EmptyTitle } from "#/components/ui/empty";
import { useT } from "#/lib/i18n";
import { cn } from "#/lib/utils";

/** An empty, error or placeholder state on ledger paper. */
export function StateCard({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon: ReactNode;
  title: ReactNode;
  description: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <Empty className={cn("ledger rounded-xl border border-dashed bg-card", className)}>
      <EmptyHeader>
        <EmptyMedia variant="icon">{icon}</EmptyMedia>
        <EmptyTitle>{title}</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
      {action && <EmptyContent>{action}</EmptyContent>}
    </Empty>
  );
}

export function ComingSoon() {
  const t = useT();
  return <StateCard icon={<Construction />} title={t.comingSoon.title} description={t.comingSoon.body} />;
}

/** The router's default error boundary. */
export function RouteError({ reset }: ErrorComponentProps) {
  const t = useT();
  const router = useRouter();
  return (
    <main className="mx-auto w-full max-w-3xl p-6 md:p-10">
      <StateCard
        icon={<TriangleAlert />}
        title={t.errors.title}
        description={t.errors.generic}
        action={
          <Button
            onClick={() => {
              reset();
              void router.invalidate();
            }}
          >
            {t.errors.retry}
          </Button>
        }
      />
    </main>
  );
}

export function NotFound() {
  const t = useT();
  return (
    <main className="mx-auto w-full max-w-3xl p-6 md:p-10">
      <StateCard
        icon={<FileQuestion />}
        title={t.errors.notFoundTitle}
        description={t.errors.notFoundBody}
        action={<ButtonLink to="/">{t.errors.home}</ButtonLink>}
      />
    </main>
  );
}
