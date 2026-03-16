import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  archivePositionApiPositionsPositionIdArchivePostMutation,
  getPositionApiPositionsPositionIdGetQueryKey,
  listPositionsApiPositionsGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useArchivePosition(positionId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...archivePositionApiPositionsPositionIdArchivePostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: listPositionsApiPositionsGetQueryKey() });
      queryClient.invalidateQueries({
        queryKey: getPositionApiPositionsPositionIdGetQueryKey({ path: { position_id: positionId } }),
      });
    },
  });
}
