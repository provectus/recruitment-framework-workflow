import { useQuery } from "@tanstack/react-query";
import { listCandidatesApiCandidatesGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useCandidates(options?: {
  offset?: number;
  limit?: number;
  search?: string | null;
  stage?: string | null;
  position_id?: number | null;
  sort_by?: string | null;
  sort_order?: string | null;
}) {
  return useQuery({
    ...listCandidatesApiCandidatesGetOptions({ query: options }),
  });
}
