import { FileTextIcon, CalendarIcon, UserIcon, ClockIcon, AlertCircleIcon } from "lucide-react";

import { useDocument } from "@/features/documents/hooks/use-document";
import { useDocumentContent } from "@/features/documents";
import { formatDateTime } from "@/shared/lib/format";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { DocumentContentRenderer } from "./document-content-renderer";

interface DocumentViewerProps {
  documentId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DocumentViewer({
  documentId,
  open,
  onOpenChange,
}: DocumentViewerProps) {
  const { data: document, isLoading, error } = useDocument(documentId ?? 0, {
    enabled: open && documentId !== null,
  });

  const contentState = useDocumentContent(
    document?.view_url,
    document?.content_type,
    open && !!document
  );

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

    return (
      <DocumentContentRenderer
        contentState={contentState}
        contentType={document.content_type}
        className="overflow-auto max-h-[calc(90vh-200px)] p-4 border rounded bg-background"
      />
    );
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
