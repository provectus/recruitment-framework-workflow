import { useState } from "react";
import { Copy, Check } from "lucide-react";
import { Button } from "@/shared/ui/button";

interface FeedbackDraftResult {
  feedback_text: string;
  rejection_stage: string;
}

export function FeedbackDraftResult({
  result,
}: {
  result: FeedbackDraftResult;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(result.feedback_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">
          Stage:{" "}
          <span className="font-medium text-foreground">
            {result.rejection_stage}
          </span>
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          className="gap-1.5"
        >
          {copied ? (
            <>
              <Check className="size-3.5 text-green-600" />
              Copied
            </>
          ) : (
            <>
              <Copy className="size-3.5" />
              Copy
            </>
          )}
        </Button>
      </div>

      <div className="rounded-lg border border-border bg-muted/40 px-4 py-4">
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {result.feedback_text}
        </p>
      </div>
    </div>
  );
}
