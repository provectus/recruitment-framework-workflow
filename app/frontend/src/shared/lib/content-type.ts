export const CONTENT_TYPE_MAP: Record<string, string> = {
  ".pdf": "application/pdf",
  ".docx":
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ".md": "text/markdown",
  ".txt": "text/plain",
};

export function getContentType(fileName: string): string {
  const extension = `.${fileName.split(".").pop()?.toLowerCase()}`;
  return CONTENT_TYPE_MAP[extension] || "application/octet-stream";
}
