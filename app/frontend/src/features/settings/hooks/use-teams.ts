import { useQuery } from "@tanstack/react-query";
import { listTeamsApiTeamsGetOptions } from "@/shared/api/@tanstack/react-query.gen";

export function useTeams() {
  return useQuery({
    ...listTeamsApiTeamsGetOptions(),
  });
}
