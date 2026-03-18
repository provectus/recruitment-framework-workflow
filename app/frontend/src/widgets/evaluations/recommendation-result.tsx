import { AlertTriangle } from "lucide-react";
import { Badge } from "@/shared/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
import { cn } from "@/shared/lib/utils";
import { SectionLabel } from "./evaluation-primitives";

type RecommendationValue = "hire" | "no_hire" | "needs_discussion";
type ConfidenceValue = "high" | "medium" | "low";

interface RecommendationResult {
  recommendation: RecommendationValue;
  confidence: ConfidenceValue;
  reasoning: string;
  missing_inputs: string[];
}

const RECOMMENDATION_CONFIG = {
  hire: {
    label: "Hire",
    className:
      "bg-green-100 text-green-900 border-green-300 hover:bg-green-100",
  },
  no_hire: {
    label: "No Hire",
    className: "bg-red-100 text-red-900 border-red-300 hover:bg-red-100",
  },
  needs_discussion: {
    label: "Needs Discussion",
    className:
      "bg-amber-100 text-amber-900 border-amber-300 hover:bg-amber-100",
  },
} as const satisfies Record<RecommendationValue, { label: string; className: string }>;

const CONFIDENCE_CONFIG = {
  high: {
    label: "High Confidence",
    className: "bg-primary text-primary-foreground hover:bg-primary",
  },
  medium: {
    label: "Medium Confidence",
    className: "border-border text-foreground",
  },
  low: {
    label: "Low Confidence",
    className: "border-amber-400 text-amber-700 dark:text-amber-400",
  },
} as const satisfies Record<ConfidenceValue, { label: string; className: string }>;

export function RecommendationResult({
  result,
}: {
  result: RecommendationResult;
}) {
  const recConfig = RECOMMENDATION_CONFIG[result.recommendation] ?? {
    label: result.recommendation ?? "Unknown",
    className: "bg-muted text-foreground border-border hover:bg-muted",
  };
  const confConfig = CONFIDENCE_CONFIG[result.confidence] ?? {
    label: result.confidence ?? "Unknown",
    className: "border-border text-foreground",
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Badge
          className={cn(
            "px-4 py-1.5 text-sm font-semibold rounded-full",
            recConfig.className,
          )}
        >
          {recConfig.label}
        </Badge>
        <Badge
          variant="outline"
          className={cn("rounded-full text-xs", confConfig.className)}
        >
          {confConfig.label}
        </Badge>
      </div>

      <div>
        <SectionLabel>Reasoning</SectionLabel>
        <p className="text-sm leading-relaxed">{result.reasoning}</p>
      </div>

      {(result.missing_inputs ?? []).length > 0 && (
        <Alert className="border-amber-300 bg-amber-50 text-amber-900 dark:bg-amber-950/20 dark:border-amber-800 dark:text-amber-300">
          <AlertTriangle className="size-4 text-amber-600 dark:text-amber-400" />
          <AlertTitle className="text-amber-900 dark:text-amber-300">
            Missing Inputs
          </AlertTitle>
          <AlertDescription className="text-amber-800 dark:text-amber-400">
            <p className="mb-1.5">
              This recommendation was made without the following inputs:
            </p>
            <ul className="list-disc list-inside space-y-0.5">
              {(result.missing_inputs ?? []).map((input, idx) => (
                <li key={idx}>{input}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
