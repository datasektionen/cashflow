import type { Capabilities, User } from "#/gen/cashflow/user/v1/user_pb";
import { Link } from "@tanstack/react-router";
import {
  BadgeCheck,
  BarChart3,
  BookOpenCheck,
  Banknote,
  ChevronsUpDown,
  FileText,
  Home,
  Landmark,
  LogOut,
  type LucideIcon,
  Monitor,
  Moon,
  PiggyBank,
  Receipt,
  Stamp,
  Sun,
  Wallet,
} from "lucide-react";
import { Avatar, AvatarFallback } from "#/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "#/components/ui/dropdown-menu";
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
import { type Theme, setTheme, useTheme } from "#/lib/theme";
import { Logo } from "./logo";

type NavItem = { to: string; label: string; icon: LucideIcon; show?: (c: Capabilities) => boolean };

const mine: NavItem[] = [
  { to: "/", label: "Översikt", icon: Home },
  { to: "/expenses/new", label: "Nytt utlägg", icon: Receipt },
  { to: "/invoices/new", label: "Ny faktura", icon: FileText },
];

// Mirrors the queues in Cashflow 3's admin section; each shows only to those
// who can act on it (or view everything).
const work: NavItem[] = [
  { to: "/attest", label: "Attestera", icon: Stamp, show: (c) => c.attestAll || c.attestCostCentres.length > 0 || c.viewAll },
  { to: "/confirm", label: "Bekräfta kvitton", icon: BadgeCheck, show: (c) => c.confirm || c.viewAll },
  { to: "/account", label: "Bokför", icon: BookOpenCheck, show: (c) => c.accountingAll || c.accountingCostCentres.length > 0 || c.viewAll },
  { to: "/pay", label: "Betala", icon: Banknote, show: (c) => c.pay || c.viewAll },
  { to: "/payments", label: "Utbetalningar", icon: Wallet, show: (c) => c.viewAllPayments },
];

const insight: NavItem[] = [
  { to: "/budget", label: "Budget", icon: PiggyBank },
  { to: "/stats", label: "Statistik", icon: BarChart3 },
  { to: "/fortnox", label: "Fortnox", icon: Landmark, show: (c) => c.manageFortnox },
];

function NavGroup({ label, items, capabilities }: { label: string; items: NavItem[]; capabilities: Capabilities }) {
  const visible = items.filter((item) => !item.show || item.show(capabilities));
  if (visible.length === 0) return null;
  return (
    <SidebarGroup>
      <SidebarGroupLabel className="text-sidebar-foreground/50">{label}</SidebarGroupLabel>
      <SidebarMenu>
        {visible.map((item) => (
          <SidebarMenuItem key={item.to}>
            <SidebarMenuButton
              render={<Link to={item.to} activeOptions={{ exact: item.to === "/" }} />}
              tooltip={item.label}
              className="data-[status=active]:bg-sidebar-accent data-[status=active]:text-sidebar-accent-foreground data-[status=active]:[&>svg]:text-sidebar-primary"
            >
              <item.icon />
              <span>{item.label}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
    </SidebarGroup>
  );
}

export function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function UserMenu({ user }: { user: User }) {
  const theme = useTheme();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <SidebarMenuButton size="lg" className="data-[popup-open]:bg-sidebar-accent">
            <Avatar className="size-8 rounded-lg">
              <AvatarFallback className="rounded-lg bg-sidebar-primary font-medium text-sidebar-primary-foreground">
                {initials(user.name)}
              </AvatarFallback>
            </Avatar>
            <span className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium text-sidebar-accent-foreground">{user.name}</span>
              <span className="truncate text-xs text-sidebar-foreground/60">{user.username}</span>
            </span>
            <ChevronsUpDown className="ml-auto size-4" />
          </SidebarMenuButton>
        }
      />
      <DropdownMenuContent side="top" align="start" className="w-(--anchor-width) min-w-56">
        <DropdownMenuGroup>
          <DropdownMenuLabel>{user.email}</DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuLabel>Tema</DropdownMenuLabel>
          <DropdownMenuRadioGroup value={theme} onValueChange={(value) => setTheme(value as Theme)}>
            <DropdownMenuRadioItem value="light">
              <Sun /> Ljust
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="dark">
              <Moon /> Mörkt
            </DropdownMenuRadioItem>
            <DropdownMenuRadioItem value="system">
              <Monitor /> System
            </DropdownMenuRadioItem>
          </DropdownMenuRadioGroup>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        {/* A full navigation: /logout is a server route that clears the cookie. */}
        <DropdownMenuItem render={<a href="/logout" />}>
          <LogOut /> Logga ut
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function AppSidebar({ user, capabilities }: { user: User; capabilities: Capabilities }) {
  return (
    <Sidebar variant="inset" collapsible="icon">
      <SidebarHeader className="px-3 pt-3">
        <Link to="/" className="rounded-md text-sidebar-accent-foreground outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring">
          <Logo className="group-data-[collapsible=icon]:[&>span:last-child]:hidden" />
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <NavGroup label="Mitt" items={mine} capabilities={capabilities} />
        <NavGroup label="Hantera" items={work} capabilities={capabilities} />
        <NavGroup label="Översikt" items={insight} capabilities={capabilities} />
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <UserMenu user={user} />
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
