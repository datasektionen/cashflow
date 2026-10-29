import type { LetterKey } from "@tanstack/react-hotkeys";
import type { LinkOptions } from "@tanstack/react-router";
import {
  BadgeCheck,
  Banknote,
  BarChart3,
  BookOpenCheck,
  FileText,
  Home,
  Landmark,
  type LucideIcon,
  PiggyBank,
  Receipt,
  Stamp,
  UserRound,
  Wallet,
} from "lucide-react";
import type { Capabilities } from "#/gen/cashflow/user/v1/user_pb";
import type { Messages } from "#/lib/i18n";

/**
 * The app's destinations. The sidebar, the "g <key>" shortcuts and the
 * shortcuts dialog all read this list, so a page is added in one place.
 */
export type NavItem = {
  to: LinkOptions["to"];
  label: (t: Messages) => string;
  icon: LucideIcon;
  /** Second key of the "G, <key>" sequence. */
  key: LetterKey;
  /** Who sees the item; absent means everyone. */
  show?: (c: Capabilities) => boolean;
};

export type NavGroup = {
  label: (t: Messages) => string;
  items: NavItem[];
};

// Queues show to those who can act on them, and to view-all admins.
const canAttest = (c: Capabilities) => c.attestAny || c.viewAll;
const canAccount = (c: Capabilities) => c.accountingAny || c.viewAll;

export const navigation: NavGroup[] = [
  {
    label: (t) => t.nav.groups.mine,
    items: [
      { to: "/", label: (t) => t.nav.overview, icon: Home, key: "O" },
      { to: "/expenses/new", label: (t) => t.nav.newExpense, icon: Receipt, key: "E" },
      { to: "/invoices/new", label: (t) => t.nav.newInvoice, icon: FileText, key: "I" },
    ],
  },
  {
    label: (t) => t.nav.groups.manage,
    items: [
      { to: "/attest", label: (t) => t.nav.attest, icon: Stamp, key: "A", show: canAttest },
      { to: "/confirm", label: (t) => t.nav.confirm, icon: BadgeCheck, key: "C", show: (c) => c.confirm || c.viewAll },
      { to: "/account", label: (t) => t.nav.account, icon: BookOpenCheck, key: "K", show: canAccount },
      { to: "/pay", label: (t) => t.nav.pay, icon: Banknote, key: "P", show: (c) => c.pay || c.viewAll },
      { to: "/payments", label: (t) => t.nav.payments, icon: Wallet, key: "U", show: (c) => c.viewAllPayments },
    ],
  },
  {
    label: (t) => t.nav.groups.insight,
    items: [
      { to: "/budget", label: (t) => t.nav.budget, icon: PiggyBank, key: "B" },
      { to: "/stats", label: (t) => t.nav.stats, icon: BarChart3, key: "S" },
      { to: "/fortnox", label: (t) => t.nav.fortnox, icon: Landmark, key: "F", show: (c) => c.manageFortnox },
    ],
  },
];

/** Reachable via the user menu rather than a sidebar group. */
export const profileItem: NavItem = { to: "/profile", label: (t) => t.nav.profile, icon: UserRound, key: "M" };

/** The groups with only the items this user may see; empty groups dropped. */
export function visibleNavigation(capabilities: Capabilities): NavGroup[] {
  return navigation
    .map((group) => ({ ...group, items: group.items.filter((item) => !item.show || item.show(capabilities)) }))
    .filter((group) => group.items.length > 0);
}
