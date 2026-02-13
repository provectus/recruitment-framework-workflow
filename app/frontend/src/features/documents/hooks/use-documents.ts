import { useQuery } from "@tanstack/react-query";
import { listCandidateDocumentsApiCandidatesCandidateIdDocumentsGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useDocuments(
  candidateId: number,
  options?: {
    position_id?: number | null;
    type?: string | null;
    candidate_position_id?: number | null;
  }
) {
  return useQuery({
    ...listCandidateDocumentsApiCandidatesCandidateIdDocumentsGetOptions({
      path: { candidate_id: candidateId },
      query: options,
    }),
  });
}
