import type { ReactNode } from "react";
import type { EvaluationResponse } from "@/shared/api";
import { ChevronDown, HistoryIcon, Loader2, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/shared/ui/collapsible";
import {
  getEvaluationStepLabel,
  getEvaluationStatusVariant,
  formatEvaluationStatus,
} from "@/shared/lib/evaluation-utils";
import { getStepSummary } from "@/shared/lib/evaluation-summary";
import { cn } from "@/shared/lib/utils";
import { useRerunEvaluation } from "@/features/evaluations";
import { EvaluationHistoryDialog } from "./evaluation-history-dialog";

interface EvaluationStepCardProps {
  evaluation: EvaluationResponse;
  candidatePositionId: number;
  resultContent?: ReactNode;
  disableRerun?: boolean;
  isOpen: boolean;
  onToggle: () => void;
}

export function EvaluationStepCard({
  evaluation,
  candidatePositionId,
  resultContent,
  disableRerun = false,
  isOpen,
  onToggle,
}: EvaluationStepCardProps) {
  const stepLabel = getEvaluationStepLabel(evaluation.step_type);
  const statusVariant = getEvaluationStatusVariant(evaluation.status);
  const statusLabel = formatEvaluationStatus(evaluation.status);
  const hasHistory = evaluation.version > 1;

  const summary = getStepSummary(
    evaluation.step_type,
    evaluation.result as Record<string, unknown> | null
  );

  const truncatedOneLiner =
    summary.oneLiner.length > 60
      ? summary.oneLiner.slice(0, 60) + "…"
      : summary.oneLiner;

  const rerunMutation = useRerunEvaluation(candidatePositionId);

  const canRerun =
    evaluation.status === "completed" || evaluation.status === "failed";

  const handleRerun = (e: React.MouseEvent) => {
    e.stopPropagation();
    rerunMutation.mutate({
      path: {
        candidate_position_id: candidatePositionId,
        step_type: evaluation.step_type,
      },
    });
  };

  const hasBodyContent = evaluation.error_message || resultContent;

  return (
    <Collapsible open={isOpen} onOpenChange={() => onToggle()}>
      <Card>
        <CardHeader className="pb-3">
          <CollapsibleTrigger
            className="w-full cursor-pointer rounded-md hover:bg-muted/50 -mx-1 px-1 py-0.5 transition-colors"
            asChild={false}
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <Badge variant={statusVariant} className="shrink-0">
                  {statusLabel}
                </Badge>
                <span className="text-sm font-medium shrink-0">{stepLabel}</span>
                {summary.metric !== "—" && (
                  <>
                    <span className="text-muted-foreground shrink-0">·</span>
                    <span className="text-sm shrink-0">{summary.metric}</span>
                  </>
                )}
                {truncatedOneLiner !== "—" && (
                  <>
                    <span className="text-muted-foreground shrink-0">·</span>
                    <span className="text-sm text-muted-foreground truncate">
                      {truncatedOneLiner}
                    </span>
                  </>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {canRerun && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={handleRerun}
                    disabled={disableRerun || rerunMutation.isPending}
                    className="h-7 gap-1 px-2"
                  >
                    {rerunMutation.isPending ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <RefreshCw className="size-3.5" />
                    )}
                    <span className="text-xs">Re-run</span>
                  </Button>
                )}
                {hasHistory && (
                  <EvaluationHistoryDialog
                    candidatePositionId={candidatePositionId}
                    stepType={evaluation.step_type}
                    trigger={
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 gap-1 px-2"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <HistoryIcon className="size-3.5" />
                        <span className="text-xs">History</span>
                      </Button>
                    }
                  />
                )}
                <ChevronDown
                  className={cn(
                    "h-4 w-4 transition-transform text-muted-foreground",
                    isOpen && "rotate-180"
                  )}
                />
              </div>
            </div>
          </CollapsibleTrigger>
        </CardHeader>
        {hasBodyContent && (
          <CollapsibleContent>
            <CardContent className="pt-0">
              {evaluation.error_message && (
                <p className="text-sm text-destructive">
                  {evaluation.error_message}
                </p>
              )}
              {resultContent && <div>{resultContent}</div>}
              {evaluation.completed_at && (
                <p className="text-xs text-muted-foreground mt-2">
                  Completed{" "}
                  {new Date(evaluation.completed_at).toLocaleString(undefined, {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
                </p>
              )}
            </CardContent>
          </CollapsibleContent>
        )}
      </Card>
    </Collapsible>
  );
}
