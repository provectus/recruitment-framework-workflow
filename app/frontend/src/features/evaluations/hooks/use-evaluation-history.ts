import { useQuery } from "@tanstack/react-query";
import { getEvaluationHistoryApiEvaluationsCandidatePositionIdStepTypeHistoryGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useEvaluationHistory(
  candidatePositionId: number,
  stepType: string,
  enabled: boolean
) {
  return useQuery({
    ...getEvaluationHistoryApiEvaluationsCandidatePositionIdStepTypeHistoryGetOptions(
      {
        path: { candidate_position_id: candidatePositionId, step_type: stepType },
      }
    ),
    enabled,
  });
}
