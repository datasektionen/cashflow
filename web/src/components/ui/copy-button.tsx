import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { Button } from "#/components/ui/button";
import { useT } from "#/lib/i18n";

/** Copies a value to the clipboard and confirms with a tick for a moment. */
export function CopyButton({ value, label }: { value: string; label?: string }) {
  const t = useT();
  const [copied, setCopied] = useState(false);
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-xs"
      aria-label={`${t.pay.copy}${label ? ` ${label}` : ""}`}
      title={copied ? t.pay.copied : t.pay.copy}
      onClick={async () => {
        await navigator.clipboard.writeText(value);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
    >
      {copied ? <Check className="text-success" /> : <Copy />}
    </Button>
  );
}
