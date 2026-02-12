import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createCandidateApiCandidatesPostMutation,
  listCandidatesApiCandidatesGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useCreateCandidate() {
  const queryClient = useQueryClient();
  return useMutation({
    ...createCandidateApiCandidatesPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listCandidatesApiCandidatesGetQueryKey(),
      });
    },
  });
}
