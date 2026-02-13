import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  archiveCandidateApiCandidatesCandidateIdArchivePostMutation,
  listCandidatesApiCandidatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useArchiveCandidate(candidateId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...archiveCandidateApiCandidatesCandidateIdArchivePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listCandidatesApiCandidatesGetQueryKey() });
      queryClient.invalidateQueries({
        queryKey: ["getCandidateApiCandidatesCandidateIdGet", { path: { candidate_id: candidateId } }],
      });
    },
  });
}
