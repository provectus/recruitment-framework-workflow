import { useEffect, useState } from "react";
import mammoth from "mammoth";
import DOMPurify from "dompurify";

export type ContentState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; content: string }
  | { status: "error"; error: string };

export function useDocumentContent(
  viewUrl: string | null | undefined,
  contentType: string | null | undefined,
  enabled: boolean
): ContentState {
  const [state, setState] = useState<ContentState>({ status: "idle" });

  useEffect(() => {
    if (!enabled || !viewUrl || !contentType) {
      setState({ status: "idle" });
      return;
    }

    if (contentType === "application/pdf") {
      setState({ status: "success", content: viewUrl });
      return;
    }

    setState({ status: "loading" });

    const controller = new AbortController();

    (async () => {
      try {
        const response = await fetch(viewUrl, { signal: controller.signal });
        if (!response.ok)
          throw new Error(`Failed to fetch: ${response.statusText}`);

        if (
          contentType ===
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ) {
          const arrayBuffer = await response.arrayBuffer();
          const result = await mammoth.convertToHtml({ arrayBuffer });
          setState({
            status: "success",
            content: DOMPurify.sanitize(result.value, {
              ALLOWED_TAGS: [
                "p", "b", "i", "em", "strong", "u", "a",
                "ul", "ol", "li", "br",
                "h1", "h2", "h3", "h4", "h5", "h6",
                "table", "tr", "td", "th", "thead", "tbody",
                "span", "div",
              ],
              ALLOWED_ATTR: ["href", "target", "alt", "colspan", "rowspan"],
            }),
          });
        } else {
          const text = await response.text();
          setState({ status: "success", content: text });
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setState({
            status: "error",
            error: err instanceof Error ? err.message : "Unknown error",
          });
        }
      }
    })();

    return () => controller.abort();
  }, [viewUrl, contentType, enabled]);

  return state;
}
