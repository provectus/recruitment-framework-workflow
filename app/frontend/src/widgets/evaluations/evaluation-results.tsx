import { useState, useEffect } from "react";
import { Skeleton } from "@/shared/ui/skeleton";
import { useEvaluations, useEvaluationStream } from "@/features/evaluations";
import { EvaluationStepCard } from "./evaluation-step-card";
import { ResultRenderer } from "./result-renderer";
import { HmDecisionGate } from "./hm-decision-gate";

const STEP_ORDER = [
  "cv_analysis",
  "screening_eval",
  "technical_eval",
  "recommendation",
  "feedback_gen",
] as const;

interface EvaluationResultsProps {
  candidatePositionId: number;
  candidateId: number;
  positionId: number;
  currentStage?: string;
}

export function EvaluationResults({
  candidatePositionId,
  candidateId,
  positionId,
  currentStage,
}: EvaluationResultsProps) {
  const { data, isLoading } = useEvaluations(candidatePositionId);

  const evaluations = data?.items ?? [];

  const streamEnabled = evaluations.some(
    (e) => e.status === "pending" || e.status === "running"
  );

  useEvaluationStream(candidatePositionId, streamEnabled);

  const [openPanels, setOpenPanels] = useState<Set<string>>(new Set());

  const togglePanel = (stepType: string) => {
    setOpenPanels((prev) => {
      const next = new Set(prev);
      if (next.has(stepType)) next.delete(stepType);
      else next.add(stepType);
      return next;
    });
  };

  useEffect(() => {
    setOpenPanels(new Set());
  }, [candidatePositionId]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (evaluations.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-6">
        No evaluations yet
      </p>
    );
  }

  const stepMap = new Map(evaluations.map((e) => [e.step_type, e]));

  const orderedEvaluations = STEP_ORDER.flatMap((step) => {
    const evaluation = stepMap.get(step);
    return evaluation ? [evaluation] : [];
  });

  const unorderedEvaluations = evaluations.filter(
    (e) => !STEP_ORDER.includes(e.step_type as (typeof STEP_ORDER)[number])
  );

  const allEvaluations = [...orderedEvaluations, ...unorderedEvaluations];

  const disableRerun = streamEnabled;

  const screeningEval = stepMap.get("screening_eval");
  const recommendation = stepMap.get("recommendation");

  const showDecisionAfterScreening =
    screeningEval?.status === "completed" && currentStage === "screening";
  const showDecisionAfterRecommendation =
    recommendation?.status === "completed" && currentStage === "technical";

  return (
    <div className="space-y-3">
      {allEvaluations.map((ev) => (
        <div key={ev.id}>
          <EvaluationStepCard
            evaluation={ev}
            candidatePositionId={candidatePositionId}
            disableRerun={disableRerun}
            resultContent={
              ev.result ? (
                <ResultRenderer stepType={ev.step_type} result={ev.result} />
              ) : undefined
            }
            isOpen={openPanels.has(ev.step_type)}
            onToggle={() => togglePanel(ev.step_type)}
          />
          {ev.step_type === "screening_eval" && showDecisionAfterScreening && (
            <HmDecisionGate
              candidatePositionId={candidatePositionId}
              candidateId={candidateId}
              positionId={positionId}
              evaluations={evaluations}
              currentStage={currentStage}
            />
          )}
          {ev.step_type === "recommendation" &&
            showDecisionAfterRecommendation && (
              <HmDecisionGate
                candidatePositionId={candidatePositionId}
                candidateId={candidateId}
                positionId={positionId}
                evaluations={evaluations}
                currentStage={currentStage}
              />
            )}
        </div>
      ))}
    </div>
  );
}
