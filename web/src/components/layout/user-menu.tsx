import { Link } from "@tanstack/react-router";
import { ChevronsUpDown, Keyboard, LogOut } from "lucide-react";
import { UserAvatar } from "#/components/layout/user-avatar";
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
import { SidebarMenuButton } from "#/components/ui/sidebar";
import type { User } from "#/gen/cashflow/user/v1/user_pb";
import { LOCALES, type Locale, setLocale, useLocale, useT } from "#/lib/i18n";
import { profileItem } from "#/lib/navigation";
import { setTheme, THEMES, type Theme, useTheme } from "#/lib/theme";

const LANGUAGE_NAMES: Record<Locale, string> = { sv: "Svenska", en: "English" };

export function UserMenu({ user, onShowShortcuts }: { user: User; onShowShortcuts: () => void }) {
  const t = useT();
  const theme = useTheme();
  const locale = useLocale();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <SidebarMenuButton size="lg" className="data-[popup-open]:bg-sidebar-accent">
            <UserAvatar
              name={user.name}
              username={user.username}
              className="bg-sidebar-primary text-sidebar-primary-foreground"
            />
            <span className="grid flex-1 text-left text-sm leading-tight">
              <span className="truncate font-medium text-sidebar-accent-foreground">{user.name}</span>
              <span className="truncate text-sidebar-foreground/60 text-xs">{user.username}</span>
            </span>
            <ChevronsUpDown className="ml-auto size-4" />
          </SidebarMenuButton>
        }
      />
      <DropdownMenuContent side="top" align="start" className="w-(--anchor-width) min-w-60">
        <DropdownMenuGroup>
          <DropdownMenuLabel className="truncate">{user.email}</DropdownMenuLabel>
          <DropdownMenuItem render={<Link to={profileItem.to} />}>
            <profileItem.icon /> {profileItem.label(t)}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={onShowShortcuts}>
            <Keyboard /> {t.userMenu.shortcuts}
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuLabel>{t.userMenu.theme}</DropdownMenuLabel>
          <DropdownMenuRadioGroup value={theme} onValueChange={(value: Theme) => setTheme(value)}>
            {THEMES.map((value) => (
              <DropdownMenuRadioItem key={value} value={value}>
                {t.userMenu.themes[value]}
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuLabel>{t.userMenu.language}</DropdownMenuLabel>
          <DropdownMenuRadioGroup value={locale} onValueChange={(value: Locale) => setLocale(value)}>
            {LOCALES.map((value) => (
              <DropdownMenuRadioItem key={value} value={value}>
                {LANGUAGE_NAMES[value]}
              </DropdownMenuRadioItem>
            ))}
          </DropdownMenuRadioGroup>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        {/* A full page load: /logout is a server route that clears the session cookie. */}
        <DropdownMenuItem render={<a href="/logout" />}>
          <LogOut /> {t.userMenu.logout}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
