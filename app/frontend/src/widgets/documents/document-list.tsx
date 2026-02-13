import React from "react";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";
import { useDocuments } from "@/features/documents";
import { useCandidate } from "@/features/candidates";
import { formatDate } from "@/shared/lib/format";
import type { DocumentResponse } from "@/shared/api";

interface DocumentListProps {
  candidateId: number;
  positionId?: number;
  type?: "cv" | "transcript";
  onDocumentClick?: (documentId: number) => void;
  onVersionHistoryClick?: (candidatePositionId: number) => void;
}

const TYPE_VARIANTS = {
  cv: "default",
  transcript: "secondary",
} as const;

function getDisplayFilename(document: DocumentResponse): string {
  if (document.input_method === "paste") {
    return "Pasted transcript";
  }
  return document.file_name || "Untitled document";
}

export function DocumentList({
  candidateId,
  positionId,
  type,
  onDocumentClick,
  onVersionHistoryClick,
}: DocumentListProps) {
  const { data: documents, isLoading } = useDocuments(candidateId, {
    position_id: positionId || null,
    type: type || null,
  });
  const { data: candidate } = useCandidate(candidateId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        Loading documents...
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
        No documents uploaded yet. Upload a CV or transcript to get started.
      </div>
    );
  }

  const cvVersionsByPosition = new Map<number, DocumentResponse[]>();
  documents.forEach((doc) => {
    if (doc.type === "cv") {
      const existing = cvVersionsByPosition.get(doc.candidate_position_id) || [];
      cvVersionsByPosition.set(doc.candidate_position_id, [...existing, doc]);
    }
  });

  const isCurrentCV = (document: DocumentResponse): boolean => {
    if (document.type !== "cv") return false;
    const versions = cvVersionsByPosition.get(document.candidate_position_id);
    return versions?.[0]?.id === document.id;
  };

  const hasMultipleCVVersions = (document: DocumentResponse): boolean => {
    if (document.type !== "cv") return false;
    const versions = cvVersionsByPosition.get(document.candidate_position_id);
    return (versions?.length || 0) > 1;
  };

  const positionTitleMap = new Map<number, string>();
  candidate?.positions?.forEach((pos) => {
    positionTitleMap.set(pos.candidate_position_id, pos.position_title);
  });

  const documentsByPosition = new Map<number, DocumentResponse[]>();
  documents.forEach((doc) => {
    const existing = documentsByPosition.get(doc.candidate_position_id) || [];
    documentsByPosition.set(doc.candidate_position_id, [...existing, doc]);
  });

  const sortedPositionIds = Array.from(documentsByPosition.keys()).sort((a, b) => {
    const titleA = positionTitleMap.get(a) || "";
    const titleB = positionTitleMap.get(b) || "";
    return titleA.localeCompare(titleB);
  });

  const shouldGroupByPosition = !positionId && documentsByPosition.size > 0;

  return (
    <div className="space-y-6">
      {shouldGroupByPosition ? (
        sortedPositionIds.map((candidatePositionId) => {
          const positionDocs = documentsByPosition.get(candidatePositionId) || [];
          const positionTitle = positionTitleMap.get(candidatePositionId) || "Unknown Position";

          const cvDocs = positionDocs.filter((doc) => doc.type === "cv");
          const transcriptDocs = positionDocs.filter((doc) => doc.type === "transcript");

          const transcriptsByStage = new Map<string, DocumentResponse[]>();
          transcriptDocs.forEach((doc) => {
            const stage = doc.interview_stage || "Unknown";
            const existing = transcriptsByStage.get(stage) || [];
            transcriptsByStage.set(stage, [...existing, doc]);
          });

          transcriptsByStage.forEach((docs, stage) => {
            transcriptsByStage.set(
              stage,
              docs.sort((a, b) => {
                const dateA = a.interview_date ? new Date(a.interview_date).getTime() : 0;
                const dateB = b.interview_date ? new Date(b.interview_date).getTime() : 0;
                return dateB - dateA;
              })
            );
          });

          const sortedStages = Array.from(transcriptsByStage.keys()).sort();

          const renderDocumentRow = (document: DocumentResponse) => (
            <TableRow
              key={document.id}
              onClick={() => onDocumentClick?.(document.id)}
              className={onDocumentClick ? "cursor-pointer hover:bg-muted/50" : undefined}
            >
              <TableCell>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      TYPE_VARIANTS[
                        document.type as keyof typeof TYPE_VARIANTS
                      ] || "outline"
                    }
                  >
                    {document.type.toUpperCase()}
                  </Badge>
                  {isCurrentCV(document) && (
                    <Badge variant="default" className="bg-green-600">
                      Current
                    </Badge>
                  )}
                </div>
              </TableCell>
              <TableCell className="font-medium">
                <div className="flex items-center gap-2">
                  {getDisplayFilename(document)}
                  {isCurrentCV(document) && hasMultipleCVVersions(document) && (
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0 text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        onVersionHistoryClick?.(document.candidate_position_id);
                      }}
                    >
                      Version history
                    </Button>
                  )}
                </div>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {document.type === "transcript" && document.interview_date
                  ? formatDate(document.interview_date)
                  : formatDate(document.created_at)}
              </TableCell>
              <TableCell className="text-muted-foreground">
                {document.type === "transcript" && document.interviewer_name
                  ? document.interviewer_name
                  : (document.uploaded_by_name || "Unknown")}
              </TableCell>
            </TableRow>
          );

          return (
            <div key={candidatePositionId} className="space-y-2">
              <h3 className="text-sm font-semibold text-muted-foreground">
                {positionTitle}
              </h3>
              <div className="border rounded-lg">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Filename / Stage</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Uploader</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {cvDocs.map(renderDocumentRow)}
                    {sortedStages.map((stage) => {
                      const stageDocs = transcriptsByStage.get(stage) || [];
                      return (
                        <React.Fragment key={stage}>
                          <TableRow className="bg-muted/30 hover:bg-muted/30">
                            <TableCell colSpan={4} className="font-medium text-sm">
                              {stage} Interviews
                            </TableCell>
                          </TableRow>
                          {stageDocs.map(renderDocumentRow)}
                        </React.Fragment>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </div>
          );
        })
      ) : (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Filename / Stage</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Uploader</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {documents.map((document) => (
                <TableRow
                  key={document.id}
                  onClick={() => onDocumentClick?.(document.id)}
                  className={onDocumentClick ? "cursor-pointer hover:bg-muted/50" : undefined}
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          TYPE_VARIANTS[
                            document.type as keyof typeof TYPE_VARIANTS
                          ] || "outline"
                        }
                      >
                        {document.type.toUpperCase()}
                      </Badge>
                      {isCurrentCV(document) && (
                        <Badge variant="default" className="bg-green-600">
                          Current
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {document.type === "transcript" && document.interview_stage
                        ? `${document.interview_stage} - ${getDisplayFilename(document)}`
                        : getDisplayFilename(document)}
                      {isCurrentCV(document) && hasMultipleCVVersions(document) && (
                        <Button
                          variant="link"
                          size="sm"
                          className="h-auto p-0 text-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            onVersionHistoryClick?.(document.candidate_position_id);
                          }}
                        >
                          Version history
                        </Button>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {document.type === "transcript" && document.interview_date
                      ? formatDate(document.interview_date)
                      : formatDate(document.created_at)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {document.type === "transcript" && document.interviewer_name
                      ? document.interviewer_name
                      : (document.uploaded_by_name || "Unknown")}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
