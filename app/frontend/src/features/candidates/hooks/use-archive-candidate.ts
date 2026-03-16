import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  archiveCandidateApiCandidatesCandidateIdArchivePostMutation,
  getCandidateApiCandidatesCandidateIdGetQueryKey,
  listCandidatesApiCandidatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useArchiveCandidate(candidateId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...archiveCandidateApiCandidatesCandidateIdArchivePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listCandidatesApiCandidatesGetQueryKey() });
      queryClient.invalidateQueries({
        queryKey: getCandidateApiCandidatesCandidateIdGetQueryKey({ path: { candidate_id: candidateId } }),
      });
    },
  });
}
