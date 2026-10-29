import { Camera, FileText, Loader2, RotateCcw, TriangleAlert, Upload, X } from "lucide-react";
import { type ReactNode, useRef, useState } from "react";
import { Button } from "#/components/ui/button";
import { useT } from "#/lib/i18n";
import { pdfPageCount, toUploadable, UploadError, uploadFile } from "#/lib/upload";
import { cn } from "#/lib/utils";
import { useFieldContext } from "./context";
import { FieldShell, useClearServerError } from "./field-shell";

/**
 * One file in a claim form: either already attached to the claim (existingId)
 * or new, going through converting → uploading → done (or error).
 */
export type FileItem = {
  key: string;
  name: string;
  contentType: string;
  previewUrl: string;
  status: "converting" | "uploading" | "done" | "error";
  progress: number;
  uploadId?: string;
  existingId?: bigint;
  pages?: number;
  errorCode?: string;
};

export const isPending = (item: FileItem) => item.status === "converting" || item.status === "uploading";

/**
 * Receipts and attachments. Files upload the moment they are added, so the
 * form submits instantly; iPhone photos are converted on the way.
 */
export function FilesField({ label, description }: { label: ReactNode; description?: ReactNode }) {
  const t = useT();
  const field = useFieldContext<FileItem[]>();
  const input = useRef<HTMLInputElement>(null);
  const camera = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const clearServerError = useClearServerError();

  const update = (key: string, change: Partial<FileItem>) =>
    field.setValue((items) => items.map((item) => (item.key === key ? { ...item, ...change } : item)));

  const start = async (key: string, original: File) => {
    try {
      update(key, { status: "converting", errorCode: undefined, progress: 0 });
      const file = await toUploadable(original);
      const pages = file.type === "application/pdf" ? await pdfPageCount(file) : undefined;
      update(key, {
        status: "uploading",
        name: file.name,
        contentType: file.type,
        previewUrl: URL.createObjectURL(file),
        pages,
      });
      const upload = await uploadFile(file, (progress) => update(key, { progress }));
      update(key, { status: "done", progress: 1, uploadId: upload.id });
    } catch (error) {
      update(key, { status: "error", errorCode: error instanceof UploadError ? error.code : "upload.failed" });
    }
  };

  const originals = useRef(new Map<string, File>());
  const add = (files: FileList | File[]) => {
    const added: FileItem[] = [...files].map((file) => {
      const key = crypto.randomUUID();
      originals.current.set(key, file);
      return { key, name: file.name, contentType: file.type, previewUrl: "", status: "converting", progress: 0 };
    });
    clearServerError();
    field.setValue((items) => [...items, ...added]);
    field.handleBlur();
    for (const item of added) void start(item.key, originals.current.get(item.key) as File);
  };

  const remove = (key: string) => {
    clearServerError();
    field.setValue((items) => items.filter((item) => item.key !== key));
  };
  const items = field.state.value;

  return (
    <FieldShell label={label} description={description} htmlFor={`${field.name}-input`}>
      <div className="flex flex-col gap-2">
        <button
          type="button"
          onClick={() => input.current?.click()}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            add(event.dataTransfer.files);
          }}
          className={cn(
            "ledger flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-8 text-center text-muted-foreground text-sm outline-none transition-colors hover:border-primary/50 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring",
            dragging && "border-primary bg-primary/5 text-foreground",
          )}
        >
          <Upload className="size-6" />
          {t.claimForm.dropHere}
        </button>
        {/* Phones open the camera directly. */}
        <Button type="button" variant="outline" className="md:hidden" onClick={() => camera.current?.click()}>
          <Camera /> {t.claimForm.takePhoto}
        </Button>
        <input
          ref={input}
          id={`${field.name}-input`}
          type="file"
          multiple
          accept="image/*,.heic,.heif,application/pdf"
          className="sr-only"
          onChange={(event) => {
            if (event.target.files) add(event.target.files);
            event.target.value = "";
          }}
        />
        <input
          ref={camera}
          type="file"
          accept="image/*"
          capture="environment"
          className="sr-only"
          tabIndex={-1}
          aria-hidden
          onChange={(event) => {
            if (event.target.files) add(event.target.files);
            event.target.value = "";
          }}
        />

        {items.length > 0 && (
          <ul className="flex flex-col gap-2">
            {items.map((item) => (
              <li key={item.key} className="flex items-center gap-3 rounded-lg border bg-card p-2">
                <div className="flex size-12 shrink-0 items-center justify-center overflow-hidden rounded-md bg-muted">
                  {item.contentType.startsWith("image/") && item.previewUrl ? (
                    <img src={item.previewUrl} alt="" className="size-full object-cover" />
                  ) : (
                    <FileText className="size-5 text-muted-foreground" />
                  )}
                </div>
                <div className="flex min-w-0 flex-1 flex-col gap-1">
                  <span className="truncate text-sm">{item.name}</span>
                  <FileStatus item={item} />
                </div>
                {item.status === "error" && originals.current.has(item.key) && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon-sm"
                    aria-label={t.claimForm.retry}
                    title={t.claimForm.retry}
                    onClick={() => void start(item.key, originals.current.get(item.key) as File)}
                  >
                    <RotateCcw />
                  </Button>
                )}
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`${t.claimForm.removeFile}: ${item.name}`}
                  title={t.claimForm.removeFile}
                  onClick={() => remove(item.key)}
                >
                  <X />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </FieldShell>
  );
}

function FileStatus({ item }: { item: FileItem }) {
  const t = useT();
  switch (item.status) {
    case "converting":
      return (
        <span className="flex items-center gap-1.5 text-muted-foreground text-xs">
          <Loader2 className="size-3 animate-spin" />
          {/\.hei[cf]$/i.test(item.name) ? t.claimForm.converting : t.claimForm.uploading}
        </span>
      );
    case "uploading":
      return (
        <span className="flex items-center gap-2 text-muted-foreground text-xs">
          <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
            <span
              className="block h-full rounded-full bg-primary transition-[width]"
              style={{ width: `${Math.round(item.progress * 100)}%` }}
            />
          </span>
          {Math.round(item.progress * 100)}%
        </span>
      );
    case "error":
      return (
        <span className="flex items-center gap-1.5 text-destructive-ink text-xs">
          <TriangleAlert className="size-3" />
          {t.validation[item.errorCode ?? ""] ?? t.claimForm.uploadFailed}
        </span>
      );
    default:
      return item.pages ? <span className="text-muted-foreground text-xs">{t.claimForm.pages(item.pages)}</span> : null;
  }
}
