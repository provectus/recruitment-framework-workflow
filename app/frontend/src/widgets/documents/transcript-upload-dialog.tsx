import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/shared/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/ui/select";
import { Input } from "@/shared/ui/input";
import { Textarea } from "@/shared/ui/textarea";
import { Label } from "@/shared/ui/label";
import { Button } from "@/shared/ui/button";
import { UploadZone } from "@/widgets/documents/upload-zone";
import { usePasteTranscript } from "@/features/documents";
import { useFileUpload } from "@/features/documents/hooks/use-file-upload";
import { getContentType } from "@/shared/lib/content-type";
import { useUsers } from "@/features/positions";
import {
  UploadStatusBanner,
  UploadProgressDisplay,
  UploadResultsSummary,
  UploadErrorDisplay,
} from "@/widgets/documents/upload-status-display";

interface TranscriptUploadDialogProps {
  candidatePositionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface TranscriptMetadata {
  interviewStage: string;
  interviewerId: string;
  interviewDate: string;
  notes: string;
}

export function TranscriptUploadDialog({
  candidatePositionId,
  open,
  onOpenChange,
  onSuccess,
}: TranscriptUploadDialogProps) {
  const [activeTab, setActiveTab] = useState<"file" | "text">("file");
  const [pastedText, setPastedText] = useState<string>("");
  const [metadata, setMetadata] = useState<TranscriptMetadata>({
    interviewStage: "",
    interviewerId: "",
    interviewDate: "",
    notes: "",
  });

  const pasteTranscriptMutation = usePasteTranscript();
  const { data: users, isLoading: usersLoading } = useUsers();

  const validateMetadata = (): string | null => {
    if (!metadata.interviewStage) return "Please select an interview stage";
    if (!metadata.interviewerId) return "Please select an interviewer";
    if (!metadata.interviewDate) return "Please select an interview date";
    return null;
  };

  const buildPresignBody = (file: File) => ({
    type: "transcript" as const,
    candidate_position_id: candidatePositionId,
    file_name: file.name,
    content_type: getContentType(file.name),
    file_size: file.size,
    interview_stage: metadata.interviewStage,
    interviewer_id: parseInt(metadata.interviewerId),
    interview_date: metadata.interviewDate,
    notes: metadata.notes || null,
  });

  const upload = useFileUpload({
    buildPresignBody,
    onSuccess: () => {
      resetMetadata();
      onSuccess?.();
    },
    onClose: (open) => {
      if (!open) resetMetadata();
      onOpenChange(open);
    },
    beforeUpload: validateMetadata,
  });

  const resetMetadata = () => {
    setPastedText("");
    setMetadata({
      interviewStage: "",
      interviewerId: "",
      interviewDate: "",
      notes: "",
    });
  };

  const handlePasteSubmit = async () => {
    const validationError = validateMetadata();
    if (validationError) {
      return;
    }

    if (!pastedText.trim()) {
      return;
    }

    try {
      await pasteTranscriptMutation.mutateAsync({
        body: {
          candidate_position_id: candidatePositionId,
          content: pastedText,
          interview_stage: metadata.interviewStage,
          interviewer_id: parseInt(metadata.interviewerId),
          interview_date: metadata.interviewDate,
          notes: metadata.notes || null,
        },
      });

      onOpenChange(false);
      resetMetadata();
      onSuccess?.();
    } catch (error) {
      console.error("Paste transcript error:", error);
    }
  };

  const handleClose = () => {
    if (!upload.isUploading) {
      onOpenChange(false);
      upload.resetState();
      resetMetadata();
    }
  };

  const isFormDisabled = upload.isUploading || upload.uploadState === "success";

  return (
    <Dialog open={open} onOpenChange={upload.canClose ? handleClose : undefined}>
      <DialogContent showCloseButton={upload.canClose}>
        <DialogHeader>
          <DialogTitle>Add Transcript</DialogTitle>
          <DialogDescription>
            Upload transcript files or paste transcript text. Select multiple files to create separate transcripts with the same metadata.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="interview-stage">
                Interview Stage <span className="text-destructive">*</span>
              </Label>
              <Select
                value={metadata.interviewStage}
                onValueChange={(value) =>
                  setMetadata({ ...metadata, interviewStage: value })
                }
                disabled={isFormDisabled}
              >
                <SelectTrigger id="interview-stage">
                  <SelectValue placeholder="Select stage" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Screening">Screening</SelectItem>
                  <SelectItem value="Technical">Technical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="interviewer">
                Interviewer <span className="text-destructive">*</span>
              </Label>
              <Select
                value={metadata.interviewerId}
                onValueChange={(value) =>
                  setMetadata({ ...metadata, interviewerId: value })
                }
                disabled={isFormDisabled || usersLoading}
              >
                <SelectTrigger id="interviewer">
                  <SelectValue
                    placeholder={usersLoading ? "Loading..." : "Select interviewer"}
                  />
                </SelectTrigger>
                <SelectContent>
                  {users?.map((user) => (
                    <SelectItem key={user.id} value={user.id.toString()}>
                      {user.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="interview-date">
                Interview Date <span className="text-destructive">*</span>
              </Label>
              <Input
                id="interview-date"
                type="date"
                value={metadata.interviewDate}
                onChange={(e) =>
                  setMetadata({ ...metadata, interviewDate: e.target.value })
                }
                disabled={isFormDisabled}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="notes">Notes (Optional)</Label>
              <Input
                id="notes"
                placeholder="Add notes..."
                value={metadata.notes}
                onChange={(e) =>
                  setMetadata({ ...metadata, notes: e.target.value })
                }
                disabled={isFormDisabled}
              />
            </div>
          </div>

          {upload.uploadState !== "success" && upload.uploadState !== "error" && (
            <Tabs
              value={activeTab}
              onValueChange={(value) => setActiveTab(value as "file" | "text")}
            >
              <TabsList>
                <TabsTrigger value="file" disabled={upload.isUploading}>
                  Upload File
                </TabsTrigger>
                <TabsTrigger value="text" disabled={upload.isUploading}>
                  Paste Text
                </TabsTrigger>
              </TabsList>

              <TabsContent value="file" className="mt-4">
                <UploadZone
                  acceptedFormats={[".pdf", ".docx", ".md", ".txt"]}
                  maxSizeBytes={26_214_400}
                  onFileSelected={upload.handleFileSelected}
                  onFilesSelected={upload.handleFilesSelected}
                  onUploadProgress={upload.setUploadProgress}
                  uploadUrl={upload.uploadUrl || undefined}
                  onUploadComplete={upload.handleUploadComplete}
                  onUploadError={upload.handleUploadError}
                  disabled={upload.isUploading}
                  multiple={true}
                />
              </TabsContent>

              <TabsContent value="text" className="mt-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="transcript-text">Transcript Text</Label>
                  <Textarea
                    id="transcript-text"
                    placeholder="Paste transcript content here..."
                    value={pastedText}
                    onChange={(e) => setPastedText(e.target.value)}
                    disabled={upload.isUploading}
                    className="min-h-[200px]"
                  />
                </div>
                <div className="flex justify-end">
                  <Button
                    onClick={handlePasteSubmit}
                    disabled={upload.isUploading || !pastedText.trim()}
                  >
                    {upload.isUploading ? "Saving..." : "Save Transcript"}
                  </Button>
                </div>
              </TabsContent>
            </Tabs>
          )}

          <UploadStatusBanner
            uploadState={upload.uploadState}
            statusMessage={upload.getStatusMessage()}
          />

          {upload.isBulkUpload && upload.uploadState === "uploading" && (
            <UploadProgressDisplay fileProgress={upload.fileProgress} />
          )}

          {upload.uploadState === "success" && upload.isBulkUpload && (
            <UploadResultsSummary
              results={upload.uploadResults}
              title="Upload Summary:"
            />
          )}

          {upload.uploadState === "error" && upload.errorMessage && (
            <UploadErrorDisplay
              errorMessage={upload.errorMessage}
              isBulkUpload={upload.isBulkUpload}
              uploadResults={upload.uploadResults}
              onRetry={upload.handleRetry}
              onClose={handleClose}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
