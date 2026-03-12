import { useQuery } from "@tanstack/react-query";
import mammoth from "mammoth";
import DOMPurify from "dompurify";

export type ContentState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; content: string }
  | { status: "error"; error: string };

const DOCX_MIME =
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

async function fetchDocumentContent(
  viewUrl: string,
  contentType: string
): Promise<string> {
  if (contentType === "application/pdf") {
    return viewUrl;
  }

  const response = await fetch(viewUrl);
  if (!response.ok) {
    throw new Error(`Failed to fetch: ${response.statusText}`);
  }

  if (contentType === DOCX_MIME) {
    const arrayBuffer = await response.arrayBuffer();
    const result = await mammoth.convertToHtml({ arrayBuffer });
    return DOMPurify.sanitize(result.value, {
      ALLOWED_TAGS: [
        "p", "b", "i", "em", "strong", "u", "a",
        "ul", "ol", "li", "br",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "table", "tr", "td", "th", "thead", "tbody",
        "span", "div",
      ],
      ALLOWED_ATTR: ["href", "target", "alt", "colspan", "rowspan"],
    });
  }

  return response.text();
}

export function useDocumentContent(
  viewUrl: string | null | undefined,
  contentType: string | null | undefined,
  enabled: boolean
): ContentState {
  const { data, isLoading, error } = useQuery({
    queryKey: ["document-content", viewUrl, contentType],
    queryFn: () => fetchDocumentContent(viewUrl!, contentType!),
    enabled: enabled && !!viewUrl && !!contentType,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });

  if (!enabled || !viewUrl || !contentType) {
    return { status: "idle" };
  }
  if (isLoading) {
    return { status: "loading" };
  }
  if (error) {
    return {
      status: "error",
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
  if (data !== undefined) {
    return { status: "success", content: data };
  }
  return { status: "idle" };
}
