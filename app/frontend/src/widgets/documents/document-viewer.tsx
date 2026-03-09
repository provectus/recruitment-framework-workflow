import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import mammoth from "mammoth";
import DOMPurify from "dompurify";
import { FileTextIcon, CalendarIcon, UserIcon, ClockIcon, AlertCircleIcon } from "lucide-react";

import { useDocument } from "@/features/documents/hooks/use-document";
import { formatDateTime } from "@/shared/lib/format";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";

interface DocumentViewerProps {
  documentId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type ContentState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; content: string }
  | { status: "error"; error: string };

export function DocumentViewer({
  documentId,
  open,
  onOpenChange,
}: DocumentViewerProps) {
  const [contentState, setContentState] = useState<ContentState>({
    status: "idle",
  });

  const { data: document, isLoading, error } = useDocument(documentId ?? 0, {
    enabled: open && documentId !== null,
  });

  useEffect(() => {
    if (!document || !open) {
      setContentState({ status: "idle" });
      return;
    }

    const fetchAndRenderContent = async () => {
      setContentState({ status: "loading" });

      try {
        const contentType = document.content_type.toLowerCase();

        if (contentType === "application/pdf") {
          setContentState({ status: "success", content: "" });
          return;
        }

        if (
          contentType ===
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ) {
          const response = await fetch(document.view_url);
          if (!response.ok) {
            throw new Error(`Failed to fetch DOCX: ${response.statusText}`);
          }
          const arrayBuffer = await response.arrayBuffer();
          const result = await mammoth.convertToHtml({ arrayBuffer });
          const sanitizedHtml = DOMPurify.sanitize(result.value, {
            ALLOWED_TAGS: [
              "p", "b", "i", "em", "strong", "u", "a",
              "ul", "ol", "li", "br",
              "h1", "h2", "h3", "h4", "h5", "h6",
              "table", "tr", "td", "th", "thead", "tbody",
              "span", "div",
            ],
            ALLOWED_ATTR: [
              "href", "target", "alt", "colspan", "rowspan",
            ],
          });
          setContentState({ status: "success", content: sanitizedHtml });
          return;
        }

        if (contentType === "text/markdown" || contentType === "text/plain") {
          const response = await fetch(document.view_url);
          if (!response.ok) {
            throw new Error(`Failed to fetch text: ${response.statusText}`);
          }
          const text = await response.text();
          setContentState({ status: "success", content: text });
          return;
        }

        setContentState({
          status: "error",
          error: `Unsupported content type: ${contentType}`,
        });
      } catch (err) {
        setContentState({
          status: "error",
          error: err instanceof Error ? err.message : "Failed to load content",
        });
      }
    };

    fetchAndRenderContent();
  }, [document, open]);

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-full min-h-[400px]">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
            <p className="text-sm text-muted-foreground">Loading document...</p>
          </div>
        </div>
      );
    }

    if (error || !document) {
      return (
        <div className="flex items-center justify-center h-full min-h-[400px]">
          <div className="flex flex-col items-center gap-2 text-destructive">
            <AlertCircleIcon className="h-8 w-8" />
            <p className="text-sm">
              {error?.message || "Failed to load document"}
            </p>
          </div>
        </div>
      );
    }

    const contentType = document.content_type.toLowerCase();

    if (contentType === "application/pdf") {
      return (
        <iframe
          src={document.view_url}
          className="w-full h-full min-h-[calc(90vh-200px)] border-0 rounded"
          title={document.file_name || "PDF Document"}
        />
      );
    }

    if (contentState.status === "loading") {
      return (
        <div className="flex items-center justify-center h-full min-h-[400px]">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full" />
            <p className="text-sm text-muted-foreground">
              Processing content...
            </p>
          </div>
        </div>
      );
    }

    if (contentState.status === "error") {
      return (
        <div className="flex items-center justify-center h-full min-h-[400px]">
          <div className="flex flex-col items-center gap-2 text-destructive">
            <AlertCircleIcon className="h-8 w-8" />
            <p className="text-sm">{contentState.error}</p>
          </div>
        </div>
      );
    }

    if (contentState.status === "success") {
      if (
        contentType ===
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      ) {
        return (
          <div
            className="prose prose-sm max-w-none overflow-auto max-h-[calc(90vh-200px)] p-4 border rounded bg-background"
            dangerouslySetInnerHTML={{ __html: contentState.content }}
          />
        );
      }

      if (contentType === "text/markdown") {
        return (
          <div className="prose prose-sm max-w-none overflow-auto max-h-[calc(90vh-200px)] p-4 border rounded bg-background">
            <ReactMarkdown>{contentState.content}</ReactMarkdown>
          </div>
        );
      }

      if (contentType === "text/plain") {
        return (
          <pre className="font-mono text-sm overflow-auto max-h-[calc(90vh-200px)] p-4 border rounded bg-muted whitespace-pre-wrap">
            {contentState.content}
          </pre>
        );
      }
    }

    return null;
  };

  const isTranscript = document?.type === "transcript";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <FileTextIcon className="h-5 w-5" />
            {document?.file_name || "Document"}
          </DialogTitle>

          {document && (
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground mt-3">
              <div className="flex items-center gap-1.5">
                <CalendarIcon className="h-4 w-4" />
                <span className="font-mono tabular-nums">Uploaded {formatDateTime(document.created_at)}</span>
              </div>

              {document.uploaded_by_name && (
                <div className="flex items-center gap-1.5">
                  <UserIcon className="h-4 w-4" />
                  <span>{document.uploaded_by_name}</span>
                </div>
              )}

              {isTranscript && document.interview_stage && (
                <div className="flex items-center gap-1.5">
                  <span className="font-medium">Stage:</span>
                  <span>{document.interview_stage}</span>
                </div>
              )}

              {isTranscript && document.interviewer_name && (
                <div className="flex items-center gap-1.5">
                  <UserIcon className="h-4 w-4" />
                  <span>Interviewer: {document.interviewer_name}</span>
                </div>
              )}

              {isTranscript && document.interview_date && (
                <div className="flex items-center gap-1.5">
                  <ClockIcon className="h-4 w-4" />
                  <span className="font-mono tabular-nums">
                    Interview: {formatDateTime(document.interview_date)}
                  </span>
                </div>
              )}
            </div>
          )}

          {isTranscript && document?.notes && (
            <div className="text-sm mt-3 p-3 bg-muted rounded-md">
              <span className="font-medium">Notes: </span>
              <span className="text-muted-foreground">{document.notes}</span>
            </div>
          )}
        </DialogHeader>

        <div className="flex-1 overflow-hidden px-6 pb-6">{renderContent()}</div>
      </DialogContent>
    </Dialog>
  );
}
