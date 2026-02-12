import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  deleteTeamApiTeamsTeamIdDeleteMutation,
  listTeamsApiTeamsGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useDeleteTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    ...deleteTeamApiTeamsTeamIdDeleteMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listTeamsApiTeamsGetQueryKey(),
      });
    },
  });
}
