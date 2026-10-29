import { describe, expect, it } from "vitest";
import { pdfPageCount, toUploadable } from "./upload";

const pdf = (pages: number) =>
  new Blob([
    `%PDF-1.4\n1 0 obj << /Type /Pages /Count ${pages} >> endobj\n` +
      Array.from({ length: pages }, (_, i) => `${i + 2} 0 obj << /Type /Page /Parent 1 0 R >> endobj\n`).join(""),
  ]);

describe("pdfPageCount", () => {
  it("counts page objects, not the page tree", async () => {
    expect(await pdfPageCount(pdf(1))).toBe(1);
    expect(await pdfPageCount(pdf(3))).toBe(3);
  });

  it("gives up on files it can't read", async () => {
    expect(await pdfPageCount(new Blob(["not a pdf"]))).toBeUndefined();
  });
});

describe("toUploadable", () => {
  it("passes ordinary files through untouched", async () => {
    const file = new File(["x"], "kvitto.jpg", { type: "image/jpeg" });
    expect(await toUploadable(file)).toBe(file);
  });
});
