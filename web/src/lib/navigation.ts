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
  Layers,
  type LucideIcon,
  PiggyBank,
  Receipt,
  ScrollText,
  Stamp,
  UserRound,
  UsersRound,
  Wallet,
} from "lucide-react";
import { Queue } from "#/gen/cashflow/claim/v1/claim_pb";
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
  /** The work queue behind the item, whose count the sidebar shows. */
  queue?: Queue;
};

export type NavGroup = {
  label: (t: Messages) => string;
  items: NavItem[];
};

// Queues show to those who can act on them, and to view-all admins.
const canAttest = (c: Capabilities) => c.attestAny || c.viewAll;
const canAccount = (c: Capabilities) => c.accountingAny || c.viewAll;
// As the server's mayLookUpUsers: the user list and pages.
export const canLookUpUsers = (c: Capabilities) => c.pay || c.viewAll;
// Anyone who sees claims beyond their own (as ClaimQuerySet.viewable_by).
const canSeeOthers = (c: Capabilities) =>
  c.viewAll || c.pay || c.confirm || c.attestAny || c.accountingAny || c.viewCostCentres.length > 0;

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
      { to: "/attest", label: (t) => t.nav.attest, icon: Stamp, key: "A", show: canAttest, queue: Queue.ATTEST },
      {
        to: "/confirm",
        label: (t) => t.nav.confirm,
        icon: BadgeCheck,
        key: "C",
        show: (c) => c.confirm || c.viewAll,
        queue: Queue.CONFIRM,
      },
      {
        to: "/account",
        label: (t) => t.nav.account,
        icon: BookOpenCheck,
        key: "K",
        show: canAccount,
        queue: Queue.ACCOUNT,
      },
      {
        to: "/pay",
        label: (t) => t.nav.pay,
        icon: Banknote,
        key: "P",
        show: (c) => c.pay || c.viewAll,
        queue: Queue.PAY,
      },
      { to: "/claims", label: (t) => t.nav.allClaims, icon: Layers, key: "L", show: canSeeOthers },
      {
        to: "/payments",
        label: (t) => t.nav.payments,
        icon: Wallet,
        key: "U",
        // As the server's claims.Viewer.MaySeePayments.
        show: (c) => c.pay || c.viewAll || c.viewAllPayments,
      },
      { to: "/vouchers", label: (t) => t.nav.vouchers, icon: ScrollText, key: "V", show: canAccount },
      { to: "/users", label: (t) => t.nav.users, icon: UsersRound, key: "R", show: canLookUpUsers },
    ],
  },
  {
    label: (t) => t.nav.groups.insight,
    items: [
      { to: "/budget", label: (t) => t.nav.budget, icon: PiggyBank, key: "B" },
      { to: "/stats", label: (t) => t.nav.stats, icon: BarChart3, key: "S" },
      {
        to: "/fortnox",
        label: (t) => t.nav.fortnox,
        icon: Landmark,
        key: "F",
        // As the server's GetFortnoxStatus.
        show: (c) => c.manageFortnox || c.viewAll,
      },
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

/** The page at pathname, when the user may not see it; undefined otherwise. */
export function restrictedItem(pathname: string, capabilities: Capabilities): NavItem | undefined {
  return navigation
    .flatMap((group) => group.items)
    .find(
      (item) =>
        item.show &&
        item.to !== "/" &&
        (pathname === item.to || pathname.startsWith(`${item.to}/`)) &&
        !item.show(capabilities),
    );
}
