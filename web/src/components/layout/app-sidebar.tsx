import { Link } from "@tanstack/react-router";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "#/components/ui/sidebar";
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
            <SidebarGroupLabel className="text-sidebar-foreground/50">{group.label(t)}</SidebarGroupLabel>
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
