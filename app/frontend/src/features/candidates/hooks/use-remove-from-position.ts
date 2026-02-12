import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  removeFromPositionApiCandidatesCandidateIdPositionsPositionIdDeleteMutation,
  getCandidateApiCandidatesCandidateIdGetQueryKey,
  listCandidatesApiCandidatesGetQueryKey,
  listPositionsApiPositionsGetQueryKey,
  getPositionApiPositionsPositionIdGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useRemoveFromPosition(candidateId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...removeFromPositionApiCandidatesCandidateIdPositionsPositionIdDeleteMutation(),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: getCandidateApiCandidatesCandidateIdGetQueryKey({ path: { candidate_id: candidateId } }),
      });
      queryClient.invalidateQueries({
        queryKey: listCandidatesApiCandidatesGetQueryKey(),
      });
      queryClient.invalidateQueries({
        queryKey: listPositionsApiPositionsGetQueryKey(),
      });
      if (variables.path?.position_id) {
        queryClient.invalidateQueries({
          queryKey: getPositionApiPositionsPositionIdGetQueryKey({ path: { position_id: variables.path.position_id } }),
        });
      }
    },
  });
}
