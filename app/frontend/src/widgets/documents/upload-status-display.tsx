import { Progress } from "@/shared/ui/progress";
import { Button } from "@/shared/ui/button";
import { AlertCircle, CheckCircle2, FileText } from "lucide-react";
import type {
  UploadState,
  FileUploadResult,
} from "@/features/documents/hooks/use-file-upload";

interface UploadStatusBannerProps {
  uploadState: UploadState;
  statusMessage: string | null;
}

export function UploadStatusBanner({
  uploadState,
  statusMessage,
}: UploadStatusBannerProps) {
  if (!statusMessage) return null;

  return (
    <div className="flex items-center justify-center gap-2 rounded-md bg-primary/10 p-3 text-sm text-primary">
      {uploadState === "success" ? (
        <CheckCircle2 className="h-4 w-4" />
      ) : (
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      <span>{statusMessage}</span>
    </div>
  );
}

interface UploadProgressDisplayProps {
  fileProgress: Record<string, number>;
}

export function UploadProgressDisplay({
  fileProgress,
}: UploadProgressDisplayProps) {
  if (Object.keys(fileProgress).length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Upload Progress:</p>
      <div className="space-y-3 max-h-[300px] overflow-y-auto">
        {Object.entries(fileProgress).map(([fileName, progress]) => (
          <div key={fileName} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <FileText className="h-3 w-3 flex-shrink-0" />
                <span className="truncate" title={fileName}>
                  {fileName}
                </span>
              </div>
              <span className="text-muted-foreground flex-shrink-0 ml-2">
                {progress}%
              </span>
            </div>
            <Progress value={progress} className="h-1.5" />
          </div>
        ))}
      </div>
    </div>
  );
}

interface UploadResultsSummaryProps {
  results: FileUploadResult[];
  title: string;
}

export function UploadResultsSummary({
  results,
  title,
}: UploadResultsSummaryProps) {
  if (results.length === 0) return null;

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{title}</p>
      <div className="space-y-1 max-h-[200px] overflow-y-auto">
        {results.map((result, index) => (
          <div
            key={index}
            className="flex items-start gap-2 rounded-md bg-muted p-2 text-xs"
          >
            {result.success ? (
              <CheckCircle2 className="h-3 w-3 text-primary mt-0.5 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-3 w-3 text-destructive mt-0.5 flex-shrink-0" />
            )}
            <FileText className="h-3 w-3 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-medium">{result.fileName}</p>
              {!result.success && result.error && (
                <p className="text-destructive">{result.error}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface UploadErrorDisplayProps {
  errorMessage: string;
  isBulkUpload: boolean;
  uploadResults: FileUploadResult[];
  onRetry: () => void;
  onClose: () => void;
}

export function UploadErrorDisplay({
  errorMessage,
  isBulkUpload,
  uploadResults,
  onRetry,
  onClose,
}: UploadErrorDisplayProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-destructive">
        <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
        <p className="text-sm">{errorMessage}</p>
      </div>
      {isBulkUpload && uploadResults.length > 0 && (
        <UploadResultsSummary results={uploadResults} title="Upload Results:" />
      )}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={onRetry}>Retry</Button>
      </div>
    </div>
  );
}
