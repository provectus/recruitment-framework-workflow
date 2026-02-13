import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Loader2, Archive } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod/v4";
import { useCandidate, useUpdateCandidate, useArchiveCandidate } from "@/features/candidates";
import { usePositions } from "@/features/positions";
import { useDocuments } from "@/features/documents";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { CvUploadDialog } from "@/widgets/documents/cv-upload-dialog";
import { TranscriptUploadDialog } from "@/widgets/documents/transcript-upload-dialog";
import { DocumentList } from "@/widgets/documents/document-list";
import { DocumentViewer, CvVersionHistory } from "@/widgets/documents";
import { CandidatePositionsTable, AddToPositionDialog } from "@/widgets/candidates";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/shared/ui/form";
import { Input } from "@/shared/ui/input";
import { Skeleton } from "@/shared/ui/skeleton";

export const Route = createFileRoute("/_authenticated/candidates/$candidateId")({
  component: CandidateDetailPage,
});

const candidateSchema = z.object({
  full_name: z.string().min(1, "Full name is required"),
  email: z.email("Please enter a valid email"),
});

type CandidateFormData = z.infer<typeof candidateSchema>;

function CandidateDetailPage() {
  const navigate = useNavigate();
  const { candidateId } = Route.useParams();
  const candidateIdNum = Number(candidateId);
  const { data: candidate, isLoading, error } = useCandidate(candidateIdNum);
  const { data: positionsData } = usePositions();
  const updateCandidate = useUpdateCandidate(candidateIdNum);
  const archiveCandidate = useArchiveCandidate(candidateIdNum);

  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);

  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadCandidatePositionId, setUploadCandidatePositionId] = useState<number | null>(null);

  const [transcriptDialogOpen, setTranscriptDialogOpen] = useState(false);
  const [transcriptCandidatePositionId, setTranscriptCandidatePositionId] = useState<number | null>(null);

  const [viewerDocumentId, setViewerDocumentId] = useState<number | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);

  const [versionHistoryOpen, setVersionHistoryOpen] = useState(false);
  const [versionHistoryCandidatePositionId, setVersionHistoryCandidatePositionId] = useState<number | null>(null);

  const { refetch: refetchDocuments } = useDocuments(candidateIdNum);

  const form = useForm<CandidateFormData>({
    resolver: zodResolver(candidateSchema),
    defaultValues: {
      full_name: "",
      email: "",
    },
  });

  useEffect(() => {
    if (candidate) {
      form.reset({
        full_name: candidate.full_name,
        email: candidate.email,
      });
    }
  }, [candidate, form]);

  const onSubmit = async (data: CandidateFormData) => {
    const changedFields: Partial<CandidateFormData> = {};
    if (data.full_name !== candidate?.full_name) {
      changedFields.full_name = data.full_name;
    }
    if (data.email !== candidate?.email) {
      changedFields.email = data.email;
    }

    if (Object.keys(changedFields).length === 0) return;

    try {
      const result = await updateCandidate.mutateAsync({
        path: { candidate_id: candidateIdNum },
        body: changedFields,
      });
      if (result) {
        form.reset({
          full_name: result.full_name,
          email: result.email,
        });
      }
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 409) {
          form.setError("email", {
            message: "A candidate with this email already exists.",
          });
        } else if (axiosError.response?.status === 404) {
          form.setError("root", {
            message: "Candidate not found",
          });
        } else {
          console.error("Failed to update candidate:", err);
        }
      } else {
        console.error("Failed to update candidate:", err);
      }
    }
  };

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
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <Skeleton className="h-8 w-64" />
          <div className="flex gap-2">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-28" />
          </div>
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="p-6">
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
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">{candidate.full_name}</h1>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={form.handleSubmit(onSubmit)}
            disabled={updateCandidate.isPending}
          >
            {updateCandidate.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Save
          </Button>
          <Button variant="outline" onClick={() => setArchiveDialogOpen(true)}>
            <Archive className="mr-2 h-4 w-4" />
            Archive
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Candidate Details</CardTitle>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form className="space-y-4">
              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full Name</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={updateCandidate.isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input {...field} disabled={updateCandidate.isPending} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              {form.formState.errors.root && (
                <p className="text-sm font-medium text-destructive">
                  {form.formState.errors.root.message}
                </p>
              )}
            </form>
          </Form>
        </CardContent>
      </Card>

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

      <Dialog open={archiveDialogOpen} onOpenChange={setArchiveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Archive Candidate</DialogTitle>
            <DialogDescription>
              Are you sure you want to archive {candidate.full_name}? They will be hidden from the candidates list.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setArchiveDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={async () => {
                try {
                  await archiveCandidate.mutateAsync({
                    path: { candidate_id: candidateIdNum },
                  });
                  setArchiveDialogOpen(false);
                  navigate({ to: "/candidates" });
                } catch (err) {
                  console.error("Failed to archive candidate:", err);
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

      <div className="text-sm text-muted-foreground space-y-1">
        <p>Created: {new Date(candidate.created_at).toLocaleString()}</p>
        <p>Last updated: {new Date(candidate.updated_at).toLocaleString()}</p>
      </div>
    </div>
  );
}
