import { useRef, useState } from "react";
import { Progress } from "@/shared/ui/progress";
import { cn } from "@/shared/lib/utils";
import { getContentType } from "@/shared/lib/content-type";
import { Upload, FileText, AlertCircle, CheckCircle2, XCircle } from "lucide-react";

import type { FileWithStatus } from "@/shared/lib/file-types";

export type { FileWithStatus };

interface UploadZoneProps {
  acceptedFormats: string[];
  maxSizeBytes?: number;
  onFileSelected?: (file: File) => void;
  onFilesSelected?: (files: FileWithStatus[]) => void;
  onUploadProgress?: (progress: number) => void;
  uploadUrl?: string;
  onUploadComplete?: () => void;
  onUploadError?: (error: string) => void;
  disabled?: boolean;
  multiple?: boolean;
}

const DEFAULT_MAX_SIZE = 26_214_400; // 25 MB

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${Math.round(bytes / Math.pow(k, i) * 100) / 100} ${sizes[i]}`;
}

function formatAcceptedFormats(formats: string[]): string {
  const upperFormats = formats.map((f) => f.replace(".", "").toUpperCase());
  if (upperFormats.length === 1) return upperFormats[0];
  if (upperFormats.length === 2) return upperFormats.join(" or ");
  const last = upperFormats[upperFormats.length - 1];
  const rest = upperFormats.slice(0, -1);
  return `${rest.join(", ")}, or ${last}`;
}

export function UploadZone({
  acceptedFormats,
  maxSizeBytes = DEFAULT_MAX_SIZE,
  onFileSelected,
  onFilesSelected,
  onUploadProgress,
  uploadUrl,
  onUploadComplete,
  onUploadError,
  disabled = false,
  multiple = false,
}: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<FileWithStatus[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const xhrRef = useRef<XMLHttpRequest | null>(null);

  const validateFile = (file: File): string | null => {
    const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
    if (!acceptedFormats.includes(extension)) {
      return `Unsupported file format. Please upload a ${formatAcceptedFormats(acceptedFormats)} file.`;
    }

    if (file.size > maxSizeBytes) {
      return `File is too large. Maximum size is ${formatFileSize(maxSizeBytes)}.`;
    }

    return null;
  };

  const uploadToS3 = (file: File, url: string) => {
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    const xhr = new XMLHttpRequest();
    xhrRef.current = xhr;

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const progress = Math.round((event.loaded / event.total) * 100);
        setUploadProgress(progress);
        onUploadProgress?.(progress);
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200 || xhr.status === 204) {
        setIsUploading(false);
        onUploadComplete?.();
      } else {
        const errorMsg = `Upload failed with status ${xhr.status}`;
        setError(errorMsg);
        setIsUploading(false);
        onUploadError?.(errorMsg);
      }
    };

    xhr.onerror = () => {
      const errorMsg = "Network error during upload";
      setError(errorMsg);
      setIsUploading(false);
      onUploadError?.(errorMsg);
    };

    xhr.onabort = () => {
      setIsUploading(false);
    };

    xhr.open("PUT", url);
    xhr.setRequestHeader("Content-Type", getContentType(file.name));
    xhr.send(file);
  };

  const handleFiles = (files: File[]) => {
    setError(null);
    setSelectedFile(null);
    setSelectedFiles([]);
    setUploadProgress(0);

    if (multiple) {
      const filesWithStatus: FileWithStatus[] = files.map((file) => {
        const validationError = validateFile(file);
        return {
          file,
          valid: !validationError,
          error: validationError || undefined,
        };
      });
      setSelectedFiles(filesWithStatus);
      onFilesSelected?.(filesWithStatus);
    } else {
      const file = files[0];
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      setSelectedFile(file);
      onFileSelected?.(file);

      if (uploadUrl) {
        uploadToS3(file, uploadUrl);
      }
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled && !isUploading) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled || isUploading) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFiles(files);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFiles(Array.from(files));
    }
  };

  const handleClick = () => {
    if (!disabled && !isUploading) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="w-full">
      <div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        className={cn(
          "relative rounded-xl border-2 border-dashed p-10 transition-colors",
          "flex flex-col items-center justify-center gap-4",
          "cursor-pointer hover:border-primary/50",
          isDragging && "border-primary bg-primary/5",
          disabled && "cursor-not-allowed opacity-50",
          isUploading && "cursor-not-allowed",
          error && "border-destructive"
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={acceptedFormats.join(",")}
          onChange={handleFileInputChange}
          className="hidden"
          disabled={disabled || isUploading}
          multiple={multiple}
        />

        {!selectedFile && selectedFiles.length === 0 && !isUploading && (
          <>
            <Upload className="h-12 w-12 text-muted-foreground" />
            <div className="text-center">
              <p className="text-sm font-medium">
                Drag and drop your {multiple ? "files" : "file"} here, or click to browse
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Supported formats: {formatAcceptedFormats(acceptedFormats)} (max{" "}
                {formatFileSize(maxSizeBytes)})
              </p>
            </div>
          </>
        )}

        {selectedFile && !isUploading && !uploadUrl && (
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-primary" />
            <div className="text-left">
              <p className="text-sm font-medium">{selectedFile.name}</p>
              <p className="text-xs text-muted-foreground">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
          </div>
        )}

        {multiple && selectedFiles.length > 0 && !isUploading && (
          <div className="w-full space-y-2">
            <p className="text-sm font-medium">
              Selected files ({selectedFiles.length})
            </p>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {selectedFiles.map((fileWithStatus, index) => (
                <div
                  key={`${fileWithStatus.file.name}-${index}`}
                  className={cn(
                    "flex items-start gap-3 rounded-md border p-3",
                    fileWithStatus.valid ? "border-border bg-background" : "border-destructive bg-destructive/5"
                  )}
                >
                  <FileText className={cn(
                    "h-5 w-5 flex-shrink-0 mt-0.5",
                    fileWithStatus.valid ? "text-primary" : "text-destructive"
                  )} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {fileWithStatus.file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(fileWithStatus.file.size)}
                    </p>
                    {fileWithStatus.error && (
                      <p className="text-xs text-destructive mt-1">
                        {fileWithStatus.error}
                      </p>
                    )}
                  </div>
                  {fileWithStatus.valid ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                  ) : (
                    <XCircle className="h-5 w-5 text-destructive flex-shrink-0" />
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {isUploading && selectedFile && (
          <div className="w-full space-y-3">
            <div className="flex items-center gap-3">
              <FileText className="h-8 w-8 text-primary" />
              <div className="flex-1 text-left">
                <p className="text-sm font-medium">{selectedFile.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
            <div className="space-y-1">
              <Progress value={uploadProgress} className="h-2" />
              <p className="text-xs text-muted-foreground text-center">
                Uploading... {uploadProgress}%
              </p>
            </div>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-destructive">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
