import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  updatePositionRubricApiPositionsPositionIdRubricPutMutation,
  getPositionRubricApiPositionsPositionIdRubricGetQueryKey,
  listRubricVersionsApiPositionsPositionIdRubricVersionsGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useUpdatePositionRubric(positionId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...updatePositionRubricApiPositionsPositionIdRubricPutMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getPositionRubricApiPositionsPositionIdRubricGetQueryKey({
          path: { position_id: positionId },
        }),
      });
      queryClient.invalidateQueries({
        queryKey:
          listRubricVersionsApiPositionsPositionIdRubricVersionsGetQueryKey({
            path: { position_id: positionId },
          }),
      });
    },
  });
}
