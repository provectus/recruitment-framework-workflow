import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  revertRubricVersionApiPositionsPositionIdRubricRevertVersionNumberPostMutation,
  getPositionRubricApiPositionsPositionIdRubricGetQueryKey,
  listRubricVersionsApiPositionsPositionIdRubricVersionsGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useRevertRubricVersion(positionId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...revertRubricVersionApiPositionsPositionIdRubricRevertVersionNumberPostMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getPositionRubricApiPositionsPositionIdRubricGetQueryKey({
          path: { position_id: positionId },
        }),
      });
      queryClient.invalidateQueries({
        queryKey: listRubricVersionsApiPositionsPositionIdRubricVersionsGetQueryKey({
          path: { position_id: positionId },
        }),
      });
    },
  });
}
