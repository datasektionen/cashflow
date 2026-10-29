/** A file uploaded ahead of submitting a claim form (POST /files). */
export type Upload = { id: string; name: string; contentType: string; size: number };

export class UploadError extends Error {
  constructor(public code: string) {
    super(code);
  }
}

const HEIC_TYPES = ["image/heic", "image/heif"];

/**
 * iPhone photos (HEIC) become JPEG before upload, since browsers cannot show
 * HEIC and the server stays free of image libraries. The converter is a
 * large WASM module, so it loads only when a HEIC file shows up.
 */
export async function toUploadable(file: File): Promise<File> {
  const looksHeic = HEIC_TYPES.includes(file.type) || /\.hei[cf]$/i.test(file.name);
  if (!looksHeic) return file;
  const { heicTo, isHeic } = await import("heic-to");
  if (!(await isHeic(file))) return file;
  const jpeg = await heicTo({ blob: file, type: "image/jpeg", quality: 0.85 });
  return new File([jpeg], file.name.replace(/\.hei[cf]$/i, ".jpg"), { type: "image/jpeg" });
}

/** Uploads one file, reporting progress from 0 to 1. */
export function uploadFile(file: File, onProgress: (fraction: number) => void): Promise<Upload> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/files");
    xhr.responseType = "json";
    xhr.upload.onprogress = (event) => event.lengthComputable && onProgress(event.loaded / event.total);
    xhr.onload = () => {
      if (xhr.status === 200) resolve(xhr.response as Upload);
      else reject(new UploadError((xhr.response as { code?: string } | null)?.code ?? "upload.failed"));
    };
    xhr.onerror = () => reject(new UploadError("upload.network"));
    const body = new FormData();
    body.append("file", file);
    xhr.send(body);
  });
}

/**
 * Counts the pages of a PDF without a PDF library, so people see at once
 * whether all pages of an invoice came along. Good for ordinary PDFs; returns
 * undefined when it cannot tell.
 */
export async function pdfPageCount(file: Blob): Promise<number | undefined> {
  const text = new TextDecoder("latin1").decode(await file.arrayBuffer());
  const pages = text.match(/\/Type\s*\/Page(?!s)\b/g)?.length;
  return pages && pages > 0 ? pages : undefined;
}
