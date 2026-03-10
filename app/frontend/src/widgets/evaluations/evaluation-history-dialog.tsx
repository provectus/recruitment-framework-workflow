import { useState } from "react";
import type { ReactNode } from "react";
import { ClockIcon } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/ui/dialog";
import { Badge } from "@/shared/ui/badge";
import { Skeleton } from "@/shared/ui/skeleton";
import {
  getEvaluationStepLabel,
  getEvaluationStatusVariant,
  formatEvaluationStatus,
} from "@/shared/lib/evaluation-utils";
import { useEvaluationHistory } from "@/features/evaluations/hooks/use-evaluation-history";
import { ResultRenderer } from "./result-renderer";

interface EvaluationHistoryDialogProps {
  candidatePositionId: number;
  stepType: string;
  trigger: ReactNode;
}

export function EvaluationHistoryDialog({
  candidatePositionId,
  stepType,
  trigger,
}: EvaluationHistoryDialogProps) {
  const [open, setOpen] = useState(false);
  const { data, isLoading } = useEvaluationHistory(
    candidatePositionId,
    stepType,
    open
  );

  const stepLabel = getEvaluationStepLabel(stepType);
  const versions = data?.items ?? [];
  const latestVersion = versions[0]?.version ?? null;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ClockIcon className="size-4" />
            {stepLabel} History
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto pr-1">
          {isLoading && (
            <div className="space-y-3">
              {[1, 2].map((i) => (
                <Skeleton key={i} className="h-24 w-full rounded-lg" />
              ))}
            </div>
          )}

          {!isLoading && versions.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">
              No history available for this evaluation step.
            </p>
          )}

          {!isLoading && versions.length > 0 && (
            <div className="space-y-3">
              {versions.map((evaluation) => {
                const isLatest = evaluation.version === latestVersion;
                return (
                  <div
                    key={evaluation.id}
                    className={`rounded-lg border p-4 space-y-3 ${
                      isLatest ? "bg-muted/40 border-border" : "bg-background"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-muted-foreground">
                        v{evaluation.version}
                      </span>
                      <Badge variant={getEvaluationStatusVariant(evaluation.status)}>
                        {formatEvaluationStatus(evaluation.status)}
                      </Badge>
                      {isLatest && (
                        <Badge variant="secondary" className="text-xs">
                          Latest
                        </Badge>
                      )}
                      {evaluation.completed_at && (
                        <span className="text-xs text-muted-foreground ml-auto">
                          {new Date(evaluation.completed_at).toLocaleString(undefined, {
                            dateStyle: "medium",
                            timeStyle: "short",
                          })}
                        </span>
                      )}
                    </div>

                    {evaluation.error_message && (
                      <p className="text-sm text-destructive">
                        {evaluation.error_message}
                      </p>
                    )}

                    {evaluation.result && (
                      <ResultRenderer
                        stepType={evaluation.step_type}
                        result={evaluation.result}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
