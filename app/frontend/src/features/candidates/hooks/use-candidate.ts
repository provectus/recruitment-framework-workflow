import { useQuery } from "@tanstack/react-query";
import { getCandidateApiCandidatesCandidateIdGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useCandidate(candidateId: number) {
  return useQuery({
    ...getCandidateApiCandidatesCandidateIdGetOptions({ path: { candidate_id: candidateId } }),
  });
}
