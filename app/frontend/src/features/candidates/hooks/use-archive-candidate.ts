import { useMutation, useQueryClient } from "@tanstack/react-query";
import { archiveCandidateApiCandidatesCandidateIdArchivePostMutation } from "@/shared/api/@tanstack/react-query.gen";

export function useArchiveCandidate(candidateId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...archiveCandidateApiCandidatesCandidateIdArchivePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listCandidatesApiCandidatesGet"] });
      queryClient.invalidateQueries({
        queryKey: ["getCandidateApiCandidatesCandidateIdGet", { path: { candidate_id: candidateId } }],
      });
    },
  });
}
