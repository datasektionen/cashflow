import {
  ChevronLeft,
  ChevronRight,
  Download,
  ExternalLink,
  FileIcon,
  FileText,
  ImageIcon,
  Paperclip,
} from "lucide-react";
import { useState } from "react";
import { Button } from "#/components/ui/button";
import { Card } from "#/components/ui/card";
import type { File } from "#/gen/cashflow/claim/v1/claim_pb";
import { useT } from "#/lib/i18n";
import { cn } from "#/lib/utils";

const isImage = (f: File) => f.contentType.startsWith("image/");
const isPdf = (f: File) => f.contentType === "application/pdf";

/** The receipts and invoices of a claim, shown in place, one at a time. */
export function FilesViewer({ files }: { files: File[] }) {
  const t = useT();
  const [index, setIndex] = useState(0);
  const file = files[index];

  if (!file) {
    return (
      <Card className="ledger flex-row items-center justify-center gap-2 py-16 text-muted-foreground text-sm">
        <Paperclip className="size-4" /> {t.claim.noFiles}
      </Card>
    );
  }

  return (
    <Card className="gap-0 overflow-hidden py-0">
      <div className="flex items-center gap-2 border-b px-3 py-2">
        <span className="flex min-w-0 flex-1 items-center gap-2 text-sm">
          {isImage(file) ? <ImageIcon className="size-4 shrink-0" /> : <FileText className="size-4 shrink-0" />}
          <span className="truncate">{file.name}</span>
        </span>
        {files.length > 1 && (
          <span className="flex items-center gap-1 text-muted-foreground text-xs">
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={t.claim.previousFile}
              disabled={index === 0}
              onClick={() => setIndex(index - 1)}
            >
              <ChevronLeft />
            </Button>
            {t.claim.fileOf(index + 1, files.length)}
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label={t.claim.nextFile}
              disabled={index === files.length - 1}
              onClick={() => setIndex(index + 1)}
            >
              <ChevronRight />
            </Button>
          </span>
        )}
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label={t.claim.openFile}
          title={t.claim.openFile}
          nativeButton={false}
          render={<a href={file.url} target="_blank" rel="noreferrer" />}
        >
          <ExternalLink />
        </Button>
      </div>

      <div className="flex min-h-80 items-center justify-center bg-muted/40">
        {isImage(file) ? (
          <a href={file.url} target="_blank" rel="noreferrer" className="block max-h-[70vh] overflow-auto p-4">
            <img
              src={file.url}
              alt={file.name}
              className="mx-auto max-h-[65vh] w-auto rounded shadow-sm ring-1 ring-black/5"
            />
          </a>
        ) : isPdf(file) ? (
          <iframe
            src={`${file.url}#navpanes=0&view=FitH`}
            title={file.name}
            className="h-[70vh] w-full border-0 bg-white"
          />
        ) : (
          <div className="flex flex-col items-center gap-3 p-10 text-muted-foreground text-sm">
            <FileIcon className="size-10" />
            <Button variant="outline" nativeButton={false} render={<a href={file.url} download />}>
              <Download /> {file.name}
            </Button>
          </div>
        )}
      </div>

      {files.length > 1 && (
        <div className="flex gap-1.5 overflow-x-auto border-t p-2">
          {files.map((f, i) => (
            <button
              key={f.id.toString()}
              type="button"
              onClick={() => setIndex(i)}
              aria-label={f.name}
              aria-current={i === index}
              className={cn(
                "size-12 shrink-0 overflow-hidden rounded-md border-2 bg-card outline-none focus-visible:ring-2 focus-visible:ring-ring",
                i === index ? "border-primary" : "border-transparent opacity-70 hover:opacity-100",
              )}
            >
              {isImage(f) ? (
                <img src={f.url} alt="" className="size-full object-cover" />
              ) : (
                <FileText className="m-auto size-5 text-muted-foreground" />
              )}
            </button>
          ))}
        </div>
      )}
    </Card>
  );
}
