import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";
import { Skeleton } from "@/shared/ui/skeleton";
import { useDocument, useDocumentContent } from "@/features/documents";
import { DocumentContentRenderer } from "./document-content-renderer";
import { formatDate } from "@/shared/lib/format";
import type { DocumentResponse } from "@/shared/api";
import { CalendarIcon, UserIcon } from "lucide-react";

interface InlineTranscriptViewerProps {
  transcripts: DocumentResponse[];
}

function buildTabLabel(doc: DocumentResponse, allTranscripts: DocumentResponse[]): string {
  const stage = doc.interview_stage ?? "Interview";
  const sameStage = allTranscripts.filter((t) => t.interview_stage === doc.interview_stage);
  if (sameStage.length <= 1) return stage;
  if (doc.interview_date) return `${stage} – ${formatDate(doc.interview_date)}`;
  const idx = sameStage.findIndex((t) => t.id === doc.id);
  return `${stage} (${idx + 1})`;
}

function TranscriptTab({ documentId }: { documentId: number }) {
  const { data: document, isLoading: metaLoading } = useDocument(documentId, { enabled: true });
  const contentState = useDocumentContent(
    document?.view_url,
    document?.content_type,
    !!document
  );

  if (metaLoading) {
    return (
      <div className="space-y-2 p-4">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {document && (
        <div className="flex items-center gap-4 text-xs text-muted-foreground px-1">
          {document.interviewer_name && (
            <span className="flex items-center gap-1">
              <UserIcon className="h-3 w-3" />
              {document.interviewer_name}
            </span>
          )}
          {document.interview_date && (
            <span className="flex items-center gap-1">
              <CalendarIcon className="h-3 w-3" />
              {formatDate(document.interview_date)}
            </span>
          )}
        </div>
      )}
      {document?.notes && (
        <p className="text-xs text-muted-foreground italic border-l-2 border-muted pl-2">
          {document.notes}
        </p>
      )}
      <div className="max-h-[500px] overflow-y-auto rounded-md border bg-muted/10 p-4">
        <DocumentContentRenderer
          contentState={contentState}
          contentType={document?.content_type ?? "text/plain"}
        />
      </div>
    </div>
  );
}

export function InlineTranscriptViewer({ transcripts }: InlineTranscriptViewerProps) {
  const [activeTab, setActiveTab] = useState(String(transcripts[0]?.id ?? ""));

  if (transcripts.length === 0) return null;

  if (transcripts.length === 1) {
    return <TranscriptTab documentId={transcripts[0].id} />;
  }

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab}>
      <TabsList>
        {transcripts.map((doc) => (
          <TabsTrigger key={doc.id} value={String(doc.id)}>
            {buildTabLabel(doc, transcripts)}
          </TabsTrigger>
        ))}
      </TabsList>
      {transcripts.map((doc) => (
        <TabsContent key={doc.id} value={String(doc.id)}>
          {activeTab === String(doc.id) && <TranscriptTab documentId={doc.id} />}
        </TabsContent>
      ))}
    </Tabs>
  );
}
