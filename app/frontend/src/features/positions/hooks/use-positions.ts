import { useQuery } from "@tanstack/react-query";
import { listPositionsApiPositionsGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function usePositions(options?: {
  offset?: number;
  limit?: number;
  status?: string;
  team_id?: number;
}) {
  return useQuery({
    ...listPositionsApiPositionsGetOptions({ query: options }),
  });
}
