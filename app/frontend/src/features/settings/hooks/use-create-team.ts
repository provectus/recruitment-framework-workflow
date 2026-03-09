import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createTeamApiTeamsPostMutation,
  listTeamsApiTeamsGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useCreateTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    ...createTeamApiTeamsPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: listTeamsApiTeamsGetQueryKey(),
      });
    },
  });
}
