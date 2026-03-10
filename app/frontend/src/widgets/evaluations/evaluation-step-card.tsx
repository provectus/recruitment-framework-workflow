import type { ReactNode } from "react";
import type { EvaluationResponse } from "@/shared/api";
import { HistoryIcon, Loader2, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import {
  getEvaluationStepLabel,
  getEvaluationStatusVariant,
  formatEvaluationStatus,
} from "@/shared/lib/evaluation-utils";
import { useRerunEvaluation } from "@/features/evaluations";
import { EvaluationHistoryDialog } from "./evaluation-history-dialog";

interface EvaluationStepCardProps {
  evaluation: EvaluationResponse;
  candidatePositionId: number;
  resultContent?: ReactNode;
  disableRerun?: boolean;
}

export function EvaluationStepCard({
  evaluation,
  candidatePositionId,
  resultContent,
  disableRerun = false,
}: EvaluationStepCardProps) {
  const stepLabel = getEvaluationStepLabel(evaluation.step_type);
  const statusVariant = getEvaluationStatusVariant(evaluation.status);
  const statusLabel = formatEvaluationStatus(evaluation.status);
  const hasHistory = evaluation.version > 1;

  const rerunMutation = useRerunEvaluation(candidatePositionId);

  const canRerun =
    evaluation.status === "completed" || evaluation.status === "failed";

  const handleRerun = () => {
    rerunMutation.mutate({
      path: {
        candidate_position_id: candidatePositionId,
        step_type: evaluation.step_type,
      },
    });
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">{stepLabel}</CardTitle>
          <div className="flex items-center gap-2">
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
                  <Button variant="ghost" size="sm" className="h-7 gap-1 px-2">
                    <HistoryIcon className="size-3.5" />
                    <span className="text-xs">History</span>
                  </Button>
                }
              />
            )}
            <Badge variant={statusVariant}>{statusLabel}</Badge>
          </div>
        </div>
        {evaluation.completed_at && (
          <p className="text-xs text-muted-foreground">
            Completed{" "}
            {new Date(evaluation.completed_at).toLocaleString(undefined, {
              dateStyle: "medium",
              timeStyle: "short",
            })}
          </p>
        )}
      </CardHeader>
      {(evaluation.error_message || resultContent) && (
        <CardContent className="pt-0">
          {evaluation.error_message && (
            <p className="text-sm text-destructive">{evaluation.error_message}</p>
          )}
          {resultContent && <div>{resultContent}</div>}
        </CardContent>
      )}
    </Card>
  );
}
