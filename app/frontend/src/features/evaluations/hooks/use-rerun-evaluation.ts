import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  rerunEvaluationApiEvaluationsCandidatePositionIdStepTypeRerunPostMutation,
  listEvaluationsApiEvaluationsCandidatePositionIdGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";
import { getEvaluationStepLabel } from "@/shared/lib/evaluation-utils";

export function useRerunEvaluation(candidatePositionId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...rerunEvaluationApiEvaluationsCandidatePositionIdStepTypeRerunPostMutation(),
    onSuccess: (_data, variables) => {
      const stepType = variables.path?.step_type ?? "";
      toast(`Re-running ${getEvaluationStepLabel(stepType)}...`);
      queryClient.invalidateQueries({
        queryKey: listEvaluationsApiEvaluationsCandidatePositionIdGetQueryKey({
          path: { candidate_position_id: candidatePositionId },
        }),
      });
    },
  });
}
