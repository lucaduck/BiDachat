import { describe, expect, it } from "vitest";

import { validateDocument } from "./document-validation";

function documentFile(name: string, size: number) {
  return { name, size } as File;
}

describe("document upload validation", () => {
  it.each([
    "report.pdf",
    "report.docx",
    "report.txt",
    "report.csv",
    "chart.png",
    "chart.jpg",
    "chart.webp",
  ])("accepts %s", (name) => {
    expect(validateDocument(documentFile(name, 128))).toBeNull();
  });

  it("rejects unsupported, empty and oversized files", () => {
    expect(validateDocument(documentFile("report.exe", 128))).toMatch(/PDF/);
    expect(validateDocument(documentFile("report.pdf", 0))).toMatch(/vacío/);
    expect(validateDocument(documentFile("report.pdf", 20 * 1024 * 1024 + 1))).toMatch(
      /20 MB/,
    );
    expect(validateDocument(documentFile("chart.png", 4 * 1024 * 1024 + 1))).toMatch(
      /4 MB/,
    );
  });
});
