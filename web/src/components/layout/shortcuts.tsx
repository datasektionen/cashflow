import { useHotkey } from "@tanstack/react-hotkeys";
import { useNavigate } from "@tanstack/react-router";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "#/components/ui/dialog";
import { Kbd, KbdGroup } from "#/components/ui/kbd";
import type { Capabilities } from "#/gen/cashflow/user/v1/user_pb";
import { useT } from "#/lib/i18n";
import { type NavItem, profileItem, visibleNavigation } from "#/lib/navigation";

function shortcutItems(capabilities: Capabilities): NavItem[] {
  return [...visibleNavigation(capabilities).flatMap((group) => group.items), profileItem];
}

// One component per sequence keeps each useHotkey call at a stable site.
function GoTo({ item }: { item: NavItem }) {
  const navigate = useNavigate();
  useHotkey(["G", item.key], () => navigate({ to: item.to }));
  return null;
}

/** Gmail-style "g <key>" navigation plus "?" for the shortcuts dialog. */
export function GlobalHotkeys({
  capabilities,
  onShowShortcuts,
}: {
  capabilities: Capabilities;
  onShowShortcuts: () => void;
}) {
  useHotkey("Shift+/", onShowShortcuts);
  return shortcutItems(capabilities).map((item) => <GoTo key={item.to} item={item} />);
}

type DialogProps = {
  capabilities: Capabilities;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function ShortcutsDialog({ capabilities, open, onOpenChange }: DialogProps) {
  const t = useT();
  const rows: Array<{ keys: string[]; label: string }> = [
    ...shortcutItems(capabilities).map((item) => ({ keys: ["G", item.key], label: t.shortcuts.goTo(item.label(t)) })),
    { keys: ["?"], label: t.shortcuts.help },
    { keys: ["Ctrl", "B"], label: t.shortcuts.toggleSidebar },
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t.shortcuts.title}</DialogTitle>
          <DialogDescription>{t.shortcuts.description}</DialogDescription>
        </DialogHeader>
        <ul className="divide-y text-sm">
          {rows.map((row) => (
            <li key={row.label} className="flex items-center justify-between gap-4 py-2">
              <span>{row.label}</span>
              <KbdGroup>
                {row.keys.map((key) => (
                  <Kbd key={key}>{key}</Kbd>
                ))}
              </KbdGroup>
            </li>
          ))}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
