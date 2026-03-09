import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Loader2, Archive } from "lucide-react";
import { useCandidate, useArchiveCandidate } from "@/features/candidates";
import { usePositions } from "@/features/positions";
import { useDocuments } from "@/features/documents";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { CvUploadDialog } from "@/widgets/documents/cv-upload-dialog";
import { TranscriptUploadDialog } from "@/widgets/documents/transcript-upload-dialog";
import { DocumentList } from "@/widgets/documents/document-list";
import { DocumentViewer, CvVersionHistory } from "@/widgets/documents";
import { CandidatePositionsTable, AddToPositionDialog, CandidateInfoCard } from "@/widgets/candidates";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Skeleton } from "@/shared/ui/skeleton";

export const Route = createFileRoute("/_authenticated/candidates/$candidateId")({
  component: CandidateDetailPage,
});

function CandidateDetailPage() {
  const navigate = useNavigate();
  const { candidateId } = Route.useParams();
  const candidateIdNum = Number(candidateId);
  const { data: candidate, isLoading, error } = useCandidate(candidateIdNum);
  const { data: positionsData } = usePositions();
  const archiveCandidate = useArchiveCandidate(candidateIdNum);

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
  const [archiveError, setArchiveError] = useState<string | null>(null);

  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadCandidatePositionId, setUploadCandidatePositionId] = useState<number | null>(null);

  const [transcriptDialogOpen, setTranscriptDialogOpen] = useState(false);
  const [transcriptCandidatePositionId, setTranscriptCandidatePositionId] = useState<number | null>(null);

  const [viewerDocumentId, setViewerDocumentId] = useState<number | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const [versionHistoryOpen, setVersionHistoryOpen] = useState(false);
  const [versionHistoryCandidatePositionId, setVersionHistoryCandidatePositionId] = useState<number | null>(null);

  const { refetch: refetchDocuments } = useDocuments(candidateIdNum);

  const handleUploadClick = (candidatePositionId: number) => {
    setUploadCandidatePositionId(candidatePositionId);
    setUploadDialogOpen(true);
  };

  const handleTranscriptClick = (candidatePositionId: number) => {
    setTranscriptCandidatePositionId(candidatePositionId);
    setTranscriptDialogOpen(true);
  };

  const availablePositions = positionsData?.items?.filter(
    (pos) =>
      pos.status !== "closed" &&
      !candidate?.positions?.some((cp) => cp.position_id === pos.id)
  ) || [];

  if (isLoading) {
    return (
      <div className="p-8 space-y-8">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-10 w-28" />
        </div>
        <Card>
          <CardContent className="pt-6 space-y-4">
            <Skeleton className="h-6 w-full" />
            <Skeleton className="h-6 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="p-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              Candidate not found
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{candidate.full_name}</h1>
          <p className="text-sm text-muted-foreground">{candidate.email}</p>
        </div>
        <Button variant="outline" onClick={() => setArchiveDialogOpen(true)}>
          <Archive className="mr-2 h-4 w-4" />
          Archive
        </Button>
      </div>

      <CandidateInfoCard
        candidateId={candidateIdNum}
        fullName={candidate.full_name}
        email={candidate.email}
        createdAt={candidate.created_at}
        updatedAt={candidate.updated_at}
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Positions</CardTitle>
            <Button
              variant="outline"
              onClick={() => setAddDialogOpen(true)}
              disabled={availablePositions.length === 0}
            >
              Add to Position
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <CandidatePositionsTable
            positions={candidate.positions ?? []}
            candidateId={candidateIdNum}
            candidateName={candidate.full_name}
            onUploadClick={handleUploadClick}
            onTranscriptClick={handleTranscriptClick}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <DocumentList
            candidateId={candidateIdNum}
            onDocumentClick={(documentId) => {
              setViewerDocumentId(documentId);
              setViewerOpen(true);
            }}
            onVersionHistoryClick={(candidatePositionId) => {
              setVersionHistoryCandidatePositionId(candidatePositionId);
              setVersionHistoryOpen(true);
            }}
          />
        </CardContent>
      </Card>

      <AddToPositionDialog
        candidateId={candidateIdNum}
        candidateName={candidate.full_name}
        availablePositions={availablePositions}
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
      />

      <Dialog open={archiveDialogOpen} onOpenChange={(open) => {
        setArchiveDialogOpen(open);
        if (!open) setArchiveError(null);
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Archive Candidate</DialogTitle>
            <DialogDescription>
              Are you sure you want to archive {candidate.full_name}? They will be hidden from the candidates list.
            </DialogDescription>
          </DialogHeader>
          {archiveError && (
            <p className="text-sm text-destructive">{archiveError}</p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setArchiveDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                try {
                  setArchiveError(null);
                  await archiveCandidate.mutateAsync({
                    path: { candidate_id: candidateIdNum },
                  });
                  setArchiveDialogOpen(false);
                  navigate({ to: "/candidates" });
                } catch {
                  setArchiveError("Failed to archive candidate. Please try again.");
                }
              }}
              disabled={archiveCandidate.isPending}
            >
              {archiveCandidate.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Archive
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {uploadCandidatePositionId !== null && (
        <CvUploadDialog
          candidatePositionId={uploadCandidatePositionId}
          open={uploadDialogOpen}
          onOpenChange={setUploadDialogOpen}
          onSuccess={() => refetchDocuments()}
        />
      )}

      {transcriptCandidatePositionId !== null && (
        <TranscriptUploadDialog
          candidatePositionId={transcriptCandidatePositionId}
          open={transcriptDialogOpen}
          onOpenChange={setTranscriptDialogOpen}
          onSuccess={() => refetchDocuments()}
        />
      )}

      <DocumentViewer
        documentId={viewerDocumentId}
        open={viewerOpen}
        onOpenChange={setViewerOpen}
      />

      {versionHistoryCandidatePositionId !== null && (
        <CvVersionHistory
          candidateId={candidateIdNum}
          candidatePositionId={versionHistoryCandidatePositionId}
          open={versionHistoryOpen}
          onOpenChange={setVersionHistoryOpen}
          onVersionClick={(documentId) => {
            setVersionHistoryOpen(false);
            setViewerDocumentId(documentId);
            setViewerOpen(true);
          }}
        />
      )}
    </div>
  );
}
