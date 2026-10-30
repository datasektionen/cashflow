import { useQuery } from "@connectrpc/connect-query";
import { Link } from "@tanstack/react-router";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
} from "#/components/ui/sidebar";
import type { Queue } from "#/gen/cashflow/claim/v1/claim_pb";
import { getQueueCounts } from "#/gen/cashflow/claim/v1/claim-ClaimService_connectquery";
import type { Capabilities, User } from "#/gen/cashflow/user/v1/user_pb";
import { useT } from "#/lib/i18n";
import { visibleNavigation } from "#/lib/navigation";
import { Logo } from "./logo";
import { UserMenu } from "./user-menu";

type Props = {
  user: User;
  capabilities: Capabilities;
  onShowShortcuts: () => void;
};

export function AppSidebar({ user, capabilities, onShowShortcuts }: Props) {
  const t = useT();
  const counts = useQueueCounts();
  return (
    <Sidebar variant="inset" collapsible="icon">
      <SidebarHeader className="px-3 pt-3">
        <Link
          to="/"
          className="rounded-md text-sidebar-accent-foreground outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
        >
          <Logo className="group-data-[collapsible=icon]:[&>span:last-child]:hidden" />
        </Link>
      </SidebarHeader>
      <SidebarContent>
        {visibleNavigation(capabilities).map((group) => (
          <SidebarGroup key={group.label(t)}>
            <SidebarGroupLabel className="text-sidebar-foreground/75">{group.label(t)}</SidebarGroupLabel>
            <SidebarMenu>
              {group.items.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <SidebarMenuButton
                    render={<Link to={item.to} activeOptions={{ exact: item.to === "/" }} />}
                    tooltip={item.label(t)}
                    className="data-[status=active]:bg-sidebar-accent data-[status=active]:text-sidebar-accent-foreground data-[status=active]:[&>svg]:text-sidebar-primary"
                  >
                    <item.icon />
                    <span>{item.label(t)}</span>
                  </SidebarMenuButton>
                  {item.queue !== undefined && Boolean(counts.get(item.queue)) && (
                    <SidebarMenuBadge className="amount rounded-full bg-sidebar-primary/15 text-sidebar-primary">
                      {counts.get(item.queue)}
                    </SidebarMenuBadge>
                  )}
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        ))}
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <UserMenu user={user} onShowShortcuts={onShowShortcuts} />
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}

/** How many claims wait in each of the user's queues; refreshed every minute and on focus. */
function useQueueCounts(): Map<Queue, number> {
  const { data } = useQuery(getQueueCounts, {}, { refetchInterval: 60_000 });
  return new Map(data?.counts.map((c) => [c.queue, c.count]));
}
