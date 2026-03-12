import ReactMarkdown from "react-markdown";
import type { ContentState } from "@/features/documents";
import { Skeleton } from "@/shared/ui/skeleton";
import { AlertCircle } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface DocumentContentRendererProps {
  contentState: ContentState;
  contentType: string;
  className?: string;
}

export function DocumentContentRenderer({
  contentState,
  contentType,
  className,
}: DocumentContentRendererProps) {
  if (contentState.status === "idle" || contentState.status === "loading") {
    return (
      <div className={className}>
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-3/4 mb-2" />
        <Skeleton className="h-4 w-5/6" />
      </div>
    );
  }

  if (contentState.status === "error") {
    return (
      <div className={cn("flex items-center gap-2 text-destructive", className)}>
        <AlertCircle className="h-4 w-4" />
        <span className="text-sm">{contentState.error}</span>
      </div>
    );
  }

  const { content } = contentState;

  if (contentType === "application/pdf") {
    return <iframe src={content} className={cn("w-full h-full", className)} title="PDF viewer" />;
  }

  if (contentType === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
    return (
      <div
        className={cn("prose prose-sm max-w-none dark:prose-invert", className)}
        dangerouslySetInnerHTML={{ __html: content }}
      />
    );
  }

  if (contentType === "text/markdown") {
    return (
      <div className={cn("prose prose-sm max-w-none dark:prose-invert", className)}>
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    );
  }

  return (
    <pre className={cn("text-sm whitespace-pre-wrap font-mono", className)}>
      {content}
    </pre>
  );
}
