import { Badge } from "@/shared/ui/badge";
import { Progress } from "@/shared/ui/progress";
import type { EvaluationResponse } from "@/shared/api";
import {
  buildStepMap,
  getRecommendationSummary,
  getTechnicalSummary,
  STEP_ORDER,
} from "@/shared/lib/evaluation-summary";
import {
  getEvaluationStepLabel,
  formatEvaluationStatus,
} from "@/shared/lib/evaluation-utils";
import { cn } from "@/shared/lib/utils";

interface EvaluationSummaryBannerProps {
  evaluations: EvaluationResponse[];
}

const VERDICT_STYLES: Record<string, string> = {
  hire: "bg-green-100 text-green-800 border-green-200",
  no_hire: "bg-red-100 text-red-800 border-red-200",
  needs_discussion: "bg-amber-100 text-amber-800 border-amber-200",
};

const CONFIDENCE_STYLES: Record<string, string> = {
  high: "bg-green-50 text-green-700",
  medium: "bg-amber-50 text-amber-700",
  low: "bg-red-50 text-red-700",
};

const STEP_STATUS_DOT: Record<string, string> = {
  completed: "bg-green-500",
  running: "bg-blue-500 animate-pulse",
  pending: "bg-amber-400",
  failed: "bg-red-500",
};

export function EvaluationSummaryBanner({ evaluations }: EvaluationSummaryBannerProps) {
  const stepMap = buildStepMap(evaluations);
  const recSummary = getRecommendationSummary(stepMap.recommendation?.result ?? null);
  const techSummary = getTechnicalSummary(stepMap.technical_eval?.result ?? null);

  const hasAnyEvaluation = evaluations.length > 0;

  if (!hasAnyEvaluation) {
    return (
      <div className="rounded-lg border border-dashed border-muted-foreground/25 bg-muted/30 px-6 py-4">
        <p className="text-sm text-muted-foreground">No evaluations yet</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-muted/20 px-6 py-4 space-y-3">
      <div className="flex items-center gap-6 flex-wrap">
        {/* Verdict + Confidence */}
        <div className="flex items-center gap-2">
          {recSummary.verdict ? (
            <Badge
              variant="outline"
              className={cn("text-sm font-medium capitalize", VERDICT_STYLES[recSummary.verdict])}
            >
              {recSummary.verdict.replace(/_/g, " ")}
            </Badge>
          ) : (
            <span className="text-sm text-muted-foreground">Verdict pending</span>
          )}
          {recSummary.confidence && (
            <Badge
              variant="outline"
              className={cn("text-xs capitalize", CONFIDENCE_STYLES[recSummary.confidence])}
            >
              {recSummary.confidence} confidence
            </Badge>
          )}
        </div>

        {/* Technical Score */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Technical:</span>
          {techSummary.score != null ? (
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold">{techSummary.metric}</span>
              <Progress
                value={(techSummary.score / techSummary.maxScore) * 100}
                className="h-2 w-16"
              />
            </div>
          ) : (
            <span className="text-sm text-muted-foreground">—</span>
          )}
        </div>

        {/* Pipeline Progress */}
        <div className="flex items-center gap-1.5 ml-auto">
          {STEP_ORDER.map((step) => {
            const ev = stepMap[step];
            const status = ev?.status ?? "not_started";
            return (
              <div key={step} className="group relative flex flex-col items-center">
                <div
                  className={cn(
                    "h-2.5 w-2.5 rounded-full",
                    STEP_STATUS_DOT[status] ?? "bg-muted-foreground/20"
                  )}
                />
                <div className="absolute -bottom-8 hidden group-hover:block z-10 whitespace-nowrap rounded bg-popover px-2 py-1 text-xs shadow-md border">
                  {getEvaluationStepLabel(step)}
                  {ev ? ` · ${formatEvaluationStatus(ev.status)}` : " · Not started"}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* One-liner */}
      {recSummary.oneLiner !== "—" && (
        <p className="text-sm text-muted-foreground leading-relaxed">{recSummary.oneLiner}</p>
      )}
    </div>
  );
}
