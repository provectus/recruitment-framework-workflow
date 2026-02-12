import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  addToPositionApiCandidatesCandidateIdPositionsPostMutation,
  getCandidateApiCandidatesCandidateIdGetQueryKey,
  listCandidatesApiCandidatesGetQueryKey,
  listPositionsApiPositionsGetQueryKey,
  getPositionApiPositionsPositionIdGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useAddToPosition(candidateId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...addToPositionApiCandidatesCandidateIdPositionsPostMutation(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({
        queryKey: getCandidateApiCandidatesCandidateIdGetQueryKey({ path: { candidate_id: candidateId } }),
      });
      queryClient.invalidateQueries({
        queryKey: listCandidatesApiCandidatesGetQueryKey(),
      });
      queryClient.invalidateQueries({
        queryKey: listPositionsApiPositionsGetQueryKey(),
      });
      if (data?.position_id) {
        queryClient.invalidateQueries({
          queryKey: getPositionApiPositionsPositionIdGetQueryKey({ path: { position_id: data.position_id } }),
        });
      }
    },
  });
}
