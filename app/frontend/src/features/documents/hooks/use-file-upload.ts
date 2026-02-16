import { useState, useRef, useEffect } from "react";
import { usePresignUpload, useCompleteUpload } from "@/features/documents";
import { getContentType } from "@/shared/lib/content-type";
import type { FileWithStatus } from "@/widgets/documents/upload-zone";

export type UploadState =
  | "idle"
  | "presigning"
  | "uploading"
  | "completing"
  | "success"
  | "error";

export interface FileUploadResult {
  fileName: string;
  success: boolean;
  error?: string;
}

interface PresignBody {
  type: string;
  candidate_position_id: number;
  file_name: string;
  content_type: string;
  file_size: number;
  interview_stage?: string | null;
  interviewer_id?: number | null;
  interview_date?: string | null;
  notes?: string | null;
}

interface UseFileUploadOptions {
  buildPresignBody: (file: File) => PresignBody;
  onSuccess?: () => void;
  onClose: (open: boolean) => void;
  beforeUpload?: () => string | null;
}

export function useFileUpload({
  buildPresignBody,
  onSuccess,
  onClose,
  beforeUpload,
}: UseFileUploadOptions) {
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [uploadUrl, setUploadUrl] = useState<string | null>(null);
  const [documentId, setDocumentId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadResults, setUploadResults] = useState<FileUploadResult[]>([]);
  const [isBulkUpload, setIsBulkUpload] = useState(false);
  const [fileProgress, setFileProgress] = useState<Record<string, number>>({});

  const xhrRefs = useRef<XMLHttpRequest[]>([]);
  const timeoutRefs = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    const xhrs = xhrRefs.current;
    const timeouts = timeoutRefs.current;
    return () => {
      xhrs.forEach((xhr) => xhr.abort());
      timeouts.forEach((id) => clearTimeout(id));
    };
  }, []);

  const presignMutation = usePresignUpload();
  const completeMutation = useCompleteUpload();

  const resetState = () => {
    setUploadState("idle");
    setUploadUrl(null);
    setDocumentId(null);
    setErrorMessage(null);
    setUploadProgress(0);
    setUploadResults([]);
    setIsBulkUpload(false);
    setFileProgress({});
  };

  const uploadSingleFile = async (file: File): Promise<FileUploadResult> => {
    try {
      const contentType = getContentType(file.name);
      const body = buildPresignBody(file);
      const response = await presignMutation.mutateAsync({ body });

      const xhr = new XMLHttpRequest();
      xhrRefs.current.push(xhr);

      await new Promise<void>((resolve, reject) => {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percentComplete = Math.round(
              (event.loaded / event.total) * 100
            );
            setFileProgress((prev) => ({
              ...prev,
              [file.name]: percentComplete,
            }));
            setUploadProgress(percentComplete);
          }
        };
        xhr.onload = () => {
          if (xhr.status === 200 || xhr.status === 204) {
            resolve();
          } else {
            reject(new Error(`Upload failed with status ${xhr.status}`));
          }
        };
        xhr.onerror = () => reject(new Error("Network error during upload"));
        xhr.open("PUT", response.upload_url);
        xhr.setRequestHeader("Content-Type", contentType);
        xhr.send(file);
      });

      await completeMutation.mutateAsync({
        path: { document_id: response.document_id },
      });

      return { fileName: file.name, success: true };
    } catch (error) {
      console.error(`Upload failed for ${file.name}:`, error);
      return {
        fileName: file.name,
        success: false,
        error: error instanceof Error ? error.message : "Upload failed",
      };
    }
  };

  const handleFilesSelected = async (filesWithStatus: FileWithStatus[]) => {
    if (beforeUpload) {
      const validationError = beforeUpload();
      if (validationError) {
        setErrorMessage(validationError);
        setUploadState("error");
        return;
      }
    }

    const validFiles = filesWithStatus.filter((f) => f.valid).map((f) => f.file);

    if (validFiles.length === 0) {
      const firstError = filesWithStatus.find((f) => f.error)?.error;
      setErrorMessage(firstError || "No valid files selected");
      setUploadState("error");
      return;
    }

    if (validFiles.length > 1) {
      setIsBulkUpload(true);
      setUploadState("uploading");
      setErrorMessage(null);

      const results = await Promise.all(
        validFiles.map((file) => uploadSingleFile(file))
      );

      setUploadResults(results);
      const allSuccess = results.every((r) => r.success);

      if (allSuccess) {
        setUploadState("success");
        const id = setTimeout(() => {
          onClose(false);
          onSuccess?.();
          resetState();
        }, 2000);
        timeoutRefs.current.push(id);
      } else {
        setUploadState("error");
        setErrorMessage(
          `${results.filter((r) => !r.success).length} of ${results.length} files failed to upload`
        );
      }
    } else {
      setIsBulkUpload(false);
      setUploadState("uploading");
      setErrorMessage(null);

      const result = await uploadSingleFile(validFiles[0]);

      if (result.success) {
        setUploadState("success");
        const id = setTimeout(() => {
          onClose(false);
          onSuccess?.();
          resetState();
        }, 1500);
        timeoutRefs.current.push(id);
      } else {
        setUploadState("error");
        setErrorMessage(result.error || "Upload failed");
      }
    }
  };

  const handleFileSelected = async (file: File) => {
    if (beforeUpload) {
      const validationError = beforeUpload();
      if (validationError) {
        setErrorMessage(validationError);
        setUploadState("error");
        return;
      }
    }

    setUploadState("presigning");
    setErrorMessage(null);

    try {
      const body = buildPresignBody(file);
      const response = await presignMutation.mutateAsync({ body });

      setDocumentId(response.document_id);
      setUploadUrl(response.upload_url);
      setUploadState("uploading");
    } catch (error) {
      console.error("Presign error:", error);
      setErrorMessage("Failed to prepare upload. Please try again.");
      setUploadState("error");
    }
  };

  const handleUploadComplete = async () => {
    if (!documentId) {
      setErrorMessage("Missing document ID. Please try again.");
      setUploadState("error");
      return;
    }

    setUploadState("completing");

    try {
      await completeMutation.mutateAsync({
        path: { document_id: documentId },
      });

      setUploadState("success");
      const id = setTimeout(() => {
        onClose(false);
        onSuccess?.();
        resetState();
      }, 1500);
      timeoutRefs.current.push(id);
    } catch (error) {
      console.error("Complete upload error:", error);
      setErrorMessage("Failed to finalize upload. Please try again.");
      setUploadState("error");
    }
  };

  const handleUploadError = (error: string) => {
    setErrorMessage(error);
    setUploadState("error");
  };

  const handleRetry = () => {
    resetState();
  };

  const handleClose = () => {
    if (uploadState !== "uploading" && uploadState !== "completing") {
      onClose(false);
      resetState();
    }
  };

  const getStatusMessage = () => {
    if (isBulkUpload && uploadState === "uploading") {
      return `Uploading ${uploadResults.length} files...`;
    }
    switch (uploadState) {
      case "presigning":
        return "Preparing upload...";
      case "uploading":
        return `Uploading... ${uploadProgress}%`;
      case "completing":
        return "Finalizing...";
      case "success":
        return isBulkUpload
          ? "All files uploaded successfully!"
          : "Upload complete!";
      default:
        return null;
    }
  };

  const isUploading = uploadState === "uploading" || uploadState === "completing";
  const canClose = uploadState !== "uploading" && uploadState !== "completing";

  return {
    uploadState,
    uploadUrl,
    errorMessage,
    uploadProgress,
    uploadResults,
    isBulkUpload,
    fileProgress,
    isUploading,
    canClose,
    handleFileSelected,
    handleFilesSelected,
    handleUploadComplete,
    handleUploadError,
    handleRetry,
    handleClose,
    getStatusMessage,
    setUploadProgress,
    resetState,
  };
}
