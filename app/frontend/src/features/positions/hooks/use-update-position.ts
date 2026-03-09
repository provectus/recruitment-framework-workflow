import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  updatePositionApiPositionsPositionIdPatchMutation,
  getPositionApiPositionsPositionIdGetQueryKey,
  listPositionsApiPositionsGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useUpdatePosition(positionId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...updatePositionApiPositionsPositionIdPatchMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getPositionApiPositionsPositionIdGetQueryKey({ path: { position_id: positionId } }),
      });
      queryClient.invalidateQueries({
        queryKey: listPositionsApiPositionsGetQueryKey(),
      });
    },
  });
}
