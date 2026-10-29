import { createQueryOptions, useSuspenseQuery } from "@connectrpc/connect-query";
import { createFileRoute, Outlet } from "@tanstack/react-router";
import { AppSidebar } from "#/components/layout/app-sidebar";
import { Logo } from "#/components/layout/logo";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "#/components/ui/sidebar";
import { getMe } from "#/gen/cashflow/user/v1/user-UserService_connectquery";
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
  const user = data.user;
  const capabilities = data.capabilities;
  if (!user || !capabilities) throw new Error("GetMe returned no user");

  return (
    <SidebarProvider>
      <AppSidebar user={user} capabilities={capabilities} />
      <SidebarInset className="overflow-hidden">
        <header className="flex h-12 items-center gap-2 bg-sidebar px-3 text-sidebar-accent-foreground md:hidden">
          <SidebarTrigger className="text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground" />
          <Logo />
        </header>
        <Outlet />
      </SidebarInset>
    </SidebarProvider>
  );
}
