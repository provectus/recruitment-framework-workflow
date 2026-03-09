import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  deletePositionRubricApiPositionsPositionIdRubricDeleteMutation,
  getPositionRubricApiPositionsPositionIdRubricGetQueryKey,
} from "@/shared/api/@tanstack/react-query.gen";

export function useDeletePositionRubric(positionId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    ...deletePositionRubricApiPositionsPositionIdRubricDeleteMutation(),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: getPositionRubricApiPositionsPositionIdRubricGetQueryKey({
          path: { position_id: positionId },
        }),
      });
    },
  });
}
