import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Options } from "@/shared/api/sdk.gen";
import type { UpdateStageApiCandidatesCandidateIdPositionsPositionIdPatchData } from "@/shared/api/types.gen";
import {
  updateStageApiCandidatesCandidateIdPositionsPositionIdPatchMutation,
  getCandidateApiCandidatesCandidateIdGetQueryKey,
  listCandidatesApiCandidatesGetQueryKey,
  getPositionApiPositionsPositionIdGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useUpdateStage(candidateId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateStageApiCandidatesCandidateIdPositionsPositionIdPatchMutation(),
    onSuccess: (_data, variables: Options<UpdateStageApiCandidatesCandidateIdPositionsPositionIdPatchData>) => {
      queryClient.invalidateQueries({
        queryKey: getCandidateApiCandidatesCandidateIdGetQueryKey({ path: { candidate_id: candidateId } }),
      });
      queryClient.invalidateQueries({
        queryKey: listCandidatesApiCandidatesGetQueryKey(),
      });
      if (variables.path?.position_id) {
        queryClient.invalidateQueries({
          queryKey: getPositionApiPositionsPositionIdGetQueryKey({ path: { position_id: variables.path.position_id } }),
        });
      }
    },
  });
}
