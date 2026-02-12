import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  updateCandidateApiCandidatesCandidateIdPatchMutation,
  getCandidateApiCandidatesCandidateIdGetQueryKey,
  listCandidatesApiCandidatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useUpdateCandidate(candidateId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...updateCandidateApiCandidatesCandidateIdPatchMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getCandidateApiCandidatesCandidateIdGetQueryKey({ path: { candidate_id: candidateId } }),
      });
      queryClient.invalidateQueries({
        queryKey: listCandidatesApiCandidatesGetQueryKey(),
      });
    },
  });
}
