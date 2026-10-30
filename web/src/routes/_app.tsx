import { createQueryOptions, useSuspenseQuery } from "@connectrpc/connect-query";
import { createFileRoute, Outlet, useLocation } from "@tanstack/react-router";
import { Lock } from "lucide-react";
import { useState } from "react";
import { AppSidebar } from "#/components/layout/app-sidebar";
import { DemoBanner } from "#/components/layout/demo-banner";
import { Logo } from "#/components/layout/logo";
import { Page } from "#/components/layout/page";
import { GlobalHotkeys, ShortcutsDialog } from "#/components/layout/shortcuts";
import { StateCard } from "#/components/layout/states";
import { ButtonLink } from "#/components/ui/button-link";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "#/components/ui/sidebar";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
import { useT } from "#/lib/i18n";
import { type NavItem, restrictedItem } from "#/lib/navigation";
import { transport } from "#/lib/rpc";

// Every page needs a session; GetMe also creates the user's row on first login.
// An expired session redirects to SSO from the transport interceptor.
export const Route = createFileRoute("/_app")({
  loader: ({ context }) => context.queryClient.ensureQueryData(createQueryOptions(getMe, {}, { transport })),
  pendingComponent: () => null,
  component: AppLayout,
});

function AppLayout() {
  const { data } = useSuspenseQuery(getMe, {});
  const [shortcutsOpen, setShortcutsOpen] = useState(false);
  const { user, capabilities } = data;
  if (!user || !capabilities) throw new Error("GetMe returned no user");

  const showShortcuts = () => setShortcutsOpen(true);

  return (
    <SidebarProvider>
      <AppSidebar user={user} capabilities={capabilities} onShowShortcuts={showShortcuts} />
      <SidebarInset className="overflow-hidden">
        <header className="flex h-12 items-center gap-2 bg-sidebar px-3 text-sidebar-accent-foreground md:hidden">
          <SidebarTrigger className="text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground" />
          <Logo />
        </header>
        <DemoBanner />
        <Guarded capabilities={capabilities} />
      </SidebarInset>
      <GlobalHotkeys capabilities={capabilities} onShowShortcuts={showShortcuts} />
      <ShortcutsDialog capabilities={capabilities} open={shortcutsOpen} onOpenChange={setShortcutsOpen} />
    </SidebarProvider>
  );
}

/**
 * Pages for some people only (attesting, paying, people…) explain that they
 * are, instead of loading something the server will refuse.
 */
function Guarded({ capabilities }: { capabilities: Parameters<NonNullable<NavItem["show"]>>[0] }) {
  const t = useT();
  const { pathname } = useLocation();
  const blocked = restrictedItem(pathname, capabilities);
  if (!blocked) return <Outlet />;
  return (
    <Page title={blocked.label(t)}>
      <StateCard
        icon={<Lock />}
        title={t.forbidden.title}
        description={t.forbidden.body(blocked.label(t))}
        action={<ButtonLink to="/">{t.errors.home}</ButtonLink>}
        className="max-w-3xl"
      />
    </Page>
  );
}
