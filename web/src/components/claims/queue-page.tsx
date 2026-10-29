import { BadgeCheck, Banknote, BookOpenCheck, Layers, Stamp } from "lucide-react";
import { Page } from "#/components/layout/page";
import type { QueueSlug } from "#/lib/claims";
import { useT } from "#/lib/i18n";
import type { ClaimSearch } from "./claim-search";
import { ClaimsList } from "./claims-list";

const icons = { attest: Stamp, confirm: BadgeCheck, account: BookOpenCheck, pay: Banknote, all: Layers };

/** A work queue, or with queue "all", every claim the user may see. */
export function QueuePage({
  queue,
  search,
  onSearch,
}: {
  queue: QueueSlug | "all";
  search: ClaimSearch;
  onSearch: (change: Partial<ClaimSearch>) => void;
}) {
  const t = useT();
  const text = t.queues[queue];
  const Icon = icons[queue];
  return (
    <Page title={text.title} eyebrow={text.description}>
      <ClaimsList
        scope={queue === "all" ? {} : { queue }}
        search={search}
        onSearch={onSearch}
        empty={{
          // An empty queue is good news: say so with a stamp.
          icon: <Icon />,
          title: text.emptyTitle,
          body: text.emptyBody,
          action:
            queue === "all" ? undefined : <span className="stamp animate-stamp text-primary">{text.emptyTitle}</span>,
        }}
      />
    </Page>
  );
}
