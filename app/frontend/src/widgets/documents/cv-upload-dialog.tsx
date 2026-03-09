import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { UploadZone } from "@/widgets/documents/upload-zone";
import { useFileUpload } from "@/features/documents/hooks/use-file-upload";
import { getContentType } from "@/shared/lib/content-type";
import {
  UploadStatusBanner,
  UploadProgressDisplay,
  UploadResultsSummary,
  UploadErrorDisplay,
} from "@/widgets/documents/upload-status-display";

interface CvUploadDialogProps {
  candidatePositionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function CvUploadDialog({
  candidatePositionId,
  open,
  onOpenChange,
  onSuccess,
}: CvUploadDialogProps) {
  const buildPresignBody = (file: File) => ({
    type: "cv" as const,
    candidate_position_id: candidatePositionId,
    file_name: file.name,
    content_type: getContentType(file.name),
    file_size: file.size,
  });

  const upload = useFileUpload({
    buildPresignBody,
    onSuccess,
    onClose: onOpenChange,
  });

  return (
    <Dialog open={open} onOpenChange={upload.canClose ? upload.handleClose : undefined}>
      <DialogContent showCloseButton={upload.canClose}>
        <DialogHeader>
          <DialogTitle>Upload CV</DialogTitle>
          <DialogDescription>
            Upload candidate CV in PDF, DOCX, or Markdown format. Select multiple files to create CV versions.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {upload.uploadState !== "success" && upload.uploadState !== "error" && (
            <UploadZone
              acceptedFormats={[".pdf", ".docx", ".md"]}
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
              onClose={upload.handleClose}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
