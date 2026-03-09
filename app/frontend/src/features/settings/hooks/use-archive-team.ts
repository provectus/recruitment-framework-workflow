import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  archiveTeamApiTeamsTeamIdArchivePostMutation,
  listTeamsApiTeamsGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useArchiveTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    ...archiveTeamApiTeamsTeamIdArchivePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listTeamsApiTeamsGetQueryKey(),
      });
    },
  });
}
