import { Code, ConnectError } from "@connectrpc/connect";
import { createQueryOptions, useSuspenseQuery } from "@connectrpc/connect-query";
import { createFileRoute, notFound } from "@tanstack/react-router";
import { Layers, UserX } from "lucide-react";
import { BackButton } from "#/components/claim/claim-detail";
import { applySearchChange, validateClaimSearch } from "#/components/claims/claim-search";
import { ClaimsList } from "#/components/claims/claims-list";
import { StateCard } from "#/components/layout/states";
import { UserAvatar } from "#/components/layout/user-avatar";
import { PersonalStats } from "#/components/stats/personal-stats";
import { ButtonLink } from "#/components/ui/button-link";
import { Card, CardContent } from "#/components/ui/card";
import { CopyButton } from "#/components/ui/copy-button";
import { getUser } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { formatBankAccount } from "#/lib/bank";
import { useT } from "#/lib/i18n";
import { transport } from "#/lib/rpc";

export const Route = createFileRoute("/_app/users/$username")({
  validateSearch: validateClaimSearch,
  loader: async ({ context, params }) => {
    try {
      await context.queryClient.ensureQueryData(
        createQueryOptions(getUser, { username: params.username }, { transport }),
      );
    } catch (error) {
      if (ConnectError.from(error).code === Code.NotFound) throw notFound();
      throw error;
    }
  },
  notFoundComponent: UserNotFound,
  component: UserPage,
});

/** One person, for payers and admins: who they are, where to pay them, and everything they have claimed. */
function UserPage() {
  const t = useT();
  const { username } = Route.useParams();
  const search = Route.useSearch();
  const navigate = Route.useNavigate();
  const user = useSuspenseQuery(getUser, { username }).data.user;
  if (!user) throw new Error("GetUser returned no user");
  const account = user.clearingNumber ? formatBankAccount(user.clearingNumber, user.bankAccount) : "";

  return (
    <main className="mx-auto w-full max-w-6xl px-4 py-3 md:px-8 md:py-4">
      <BackButton />
      <Card size="sm" className="mt-2">
        <CardContent className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <div className="flex items-center gap-3">
            <UserAvatar name={user.name} username={user.username} className="bg-secondary" />
            <div className="flex flex-col leading-tight">
              <h1 className="font-display font-semibold text-xl">{user.name || user.username}</h1>
              <span className="text-muted-foreground text-sm">
                {user.username} · {user.email}
              </span>
            </div>
          </div>
          <div className="flex flex-col leading-tight">
            <span className="text-muted-foreground text-xs">{t.users.bank}</span>
            {account ? (
              <span className="flex items-center gap-1 font-medium">
                {user.bankName && <span className="font-normal text-muted-foreground">{user.bankName}</span>}
                <span className="amount">{account}</span>
                <CopyButton value={account} label={t.users.bank} />
              </span>
            ) : (
              <span className="text-destructive-ink text-sm">{t.users.noBank}</span>
            )}
          </div>
        </CardContent>
      </Card>
      <div className="mt-3">
        <PersonalStats username={username} />
      </div>
      <section aria-labelledby="user-claims" className="mt-4 flex flex-col gap-2">
        <h2 id="user-claims" className="font-display font-semibold text-lg">
          {t.users.claims}
        </h2>
        <ClaimsList
          scope={{ owner: username }}
          search={search}
          onSearch={(change) => navigate({ search: (prev) => applySearchChange(prev, change), replace: true })}
          empty={{ icon: <Layers />, title: t.queues.all.emptyTitle, body: t.queues.all.emptyBody }}
        />
      </section>
    </main>
  );
}

function UserNotFound() {
  const t = useT();
  return (
    <main className="mx-auto w-full max-w-3xl p-6">
      <StateCard
        icon={<UserX />}
        title={t.users.notFoundTitle}
        description={t.users.notFoundBody}
        action={<ButtonLink to="/users">{t.users.title}</ButtonLink>}
      />
    </main>
  );
}
