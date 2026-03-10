import { useQuery } from "@tanstack/react-query";
import { listEvaluationsApiEvaluationsCandidatePositionIdGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useEvaluations(candidatePositionId: number) {
  return useQuery(
    listEvaluationsApiEvaluationsCandidatePositionIdGetOptions({
      path: { candidate_position_id: candidatePositionId },
    })
  );
}
